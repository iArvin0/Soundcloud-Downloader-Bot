from __future__ import annotations

import asyncio
import html
import logging
import time
from collections import defaultdict

from telegram import Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import ContextTypes

from .config import Settings
from .downloader import AudioResult, DownloadError, MediaDownloader
from .utils import format_duration, human_size, is_valid_http_url

logger = logging.getLogger(__name__)

START_TEXT = """🎵 <b>Soundcloud Downloader Bot</b>

Send me a supported media URL and I will download its audio, convert it to
<b>MP3 320 kbps</b>, add available metadata/artwork, and send it back.

Use /help for details."""

HELP_TEXT = """🛠 <b>How to use</b>

1. Send a direct media URL supported by yt-dlp.
2. The bot extracts the best available audio.
3. FFmpeg converts it to MP3 at 320 kbps.
4. Available title, artist, metadata and artwork are embedded.
5. The MP3 is sent back in Telegram's music player.

<b>Notes</b>
• Only one URL is processed per message.
• Playlists are intentionally treated as a single-media request.
• Telegram bots currently have an upload limit for audio files, so very large MP3s cannot be sent.
• Some websites may block automated downloads, require authentication, or use DRM.
  This bot does not bypass DRM or access controls.
• Only download media you are allowed to download."""


class BotHandlers:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.downloader = MediaDownloader(
            settings.download_dir,
            settings.mp3_quality_kbps,
            settings.ffmpeg_location,
        )
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
        self.user_locks: defaultdict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message:
            await update.effective_message.reply_text(START_TEXT, parse_mode=ParseMode.HTML)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_message:
            await update.effective_message.reply_text(HELP_TEXT, parse_mode=ParseMode.HTML)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        message = update.effective_message
        user = update.effective_user
        if message is None or user is None or not message.text:
            return

        url = message.text.strip()
        if not is_valid_http_url(url):
            await message.reply_text("Please send a valid http:// or https:// media URL.")
            return

        user_lock = self.user_locks[user.id]
        if user_lock.locked():
            await message.reply_text(
                "You already have a download in progress. Please wait for it to finish."
            )
            return

        async with user_lock, self.semaphore:
            await self._process_url(update, context, url)

    async def _process_url(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str
    ) -> None:
        message = update.effective_message
        if message is None:
            return

        status = await message.reply_text("🔎 Reading media information…")
        result: AudioResult | None = None
        loop = asyncio.get_running_loop()
        last_edit = {"time": 0.0, "text": ""}

        def progress_callback(text: str) -> None:
            now = time.monotonic()
            # Throttle status edits to avoid Telegram flood limits.
            is_throttled = now - last_edit["time"] < 2.5 and "ready" not in text.lower()
            if text == last_edit["text"] or is_throttled:
                return
            last_edit["time"] = now
            last_edit["text"] = text

            async def edit() -> None:
                try:
                    await status.edit_text(f"⏳ {text}")
                except Exception:
                    logger.debug("Status edit failed", exc_info=True)

            asyncio.run_coroutine_threadsafe(edit(), loop)

        try:
            logger.info(
                "Download requested | user_id=%s | chat_id=%s | url=%s",
                update.effective_user.id if update.effective_user else None,
                update.effective_chat.id if update.effective_chat else None,
                url,
            )

            await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)
            result = await self.downloader.download(url, progress_callback)

            file_size = result.path.stat().st_size
            max_bytes = self.settings.telegram_max_file_mb * 1024 * 1024
            if file_size > max_bytes:
                await status.edit_text(
                    "❌ The MP3 was created successfully, but it is too large to upload "
                    "through the Telegram Bot API.\n\n"
                    f"File size: {human_size(file_size)}\n"
                    f"Configured upload limit: {self.settings.telegram_max_file_mb} MB"
                )
                logger.warning(
                    "Upload skipped: file too large | path=%s | bytes=%d",
                    result.path,
                    file_size,
                )
                return

            caption = self._caption(result, file_size)
            await status.edit_text("📤 Uploading MP3 to Telegram…")
            await context.bot.send_chat_action(
                chat_id=message.chat_id, action=ChatAction.UPLOAD_DOCUMENT
            )

            with result.path.open("rb") as audio:
                await message.reply_audio(
                    audio=audio,
                    filename=result.path.name,
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    title=result.title[:64],
                    performer=result.artist[:64] if result.artist != "Unknown" else None,
                    duration=result.duration,
                    read_timeout=120,
                    write_timeout=600,
                    connect_timeout=30,
                    pool_timeout=30,
                )

            await status.delete()
            logger.info("Download completed | title=%s | bytes=%d", result.title, file_size)

        except DownloadError as exc:
            logger.info("User-facing download error | url=%s | error=%s", url, exc)
            await status.edit_text(
                f"❌ <b>Download failed</b>\n\n{html.escape(str(exc))}",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            logger.exception("Unhandled request failure | url=%s", url)
            try:
                await status.edit_text(
                    "❌ An unexpected error occurred. The full traceback has been written "
                    "to the bot log."
                )
            except Exception:
                logger.debug("Failed to update error status", exc_info=True)
        finally:
            self.downloader.cleanup(result)

    @staticmethod
    def _caption(result: AudioResult, file_size: int) -> str:
        def esc(value: str, limit: int = 160) -> str:
            clipped = value if len(value) <= limit else value[: limit - 1] + "…"
            return html.escape(clipped)

        lines = [
            f"🎵 <b>{esc(result.title)}</b>",
            f"👤 {esc(result.artist)}",
            f"⏱ {format_duration(result.duration)}",
        ]

        if result.album:
            lines.append(f"💿 {esc(result.album, 120)}")
        if result.genre:
            lines.append(f"🏷 {esc(result.genre, 100)}")
        if result.upload_date:
            lines.append(f"📅 {esc(result.upload_date, 32)}")
        if result.view_count is not None:
            lines.append(f"▶️ {result.view_count:,} plays/views")
        if result.like_count is not None:
            lines.append(f"❤️ {result.like_count:,} likes")

        lines.extend(
            [
                f"💾 {human_size(file_size)}",
                f"🌐 {esc(result.source, 64)}",
                "🎧 MP3 • 320 kbps target",
                (
                    '🔗 <a href="'
                    + html.escape(result.webpage_url, quote=True)
                    + '">Open source</a>'
                ),
            ]
        )
        return "\n".join(lines)
