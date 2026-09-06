from __future__ import annotations

import asyncio
import logging
import shutil
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yt_dlp

from .utils import clean_yt_dlp_error, first_nonempty

logger = logging.getLogger(__name__)


class YTDLPLogger:
    """Route yt-dlp messages into the bot's rotating Python log."""

    def debug(self, message: str) -> None:
        # yt-dlp may send normal informational lines through debug().
        logger.debug("yt-dlp | %s", message)

    def info(self, message: str) -> None:
        logger.info("yt-dlp | %s", message)

    def warning(self, message: str) -> None:
        logger.warning("yt-dlp | %s", message)

    def error(self, message: str) -> None:
        logger.error("yt-dlp | %s", message)


ProgressCallback = Callable[[str], None]


class DownloadError(RuntimeError):
    """A user-facing media download/conversion error."""


@dataclass(slots=True)
class AudioResult:
    path: Path
    title: str
    artist: str
    duration: int | None
    source: str
    webpage_url: str
    album: str | None = None
    genre: str | None = None
    upload_date: str | None = None
    view_count: int | None = None
    like_count: int | None = None


class MediaDownloader:
    def __init__(
        self,
        base_dir: Path,
        quality_kbps: int = 320,
        ffmpeg_location: str | None = None,
    ) -> None:
        self.base_dir = base_dir
        self.quality_kbps = quality_kbps
        self.ffmpeg_location = self._normalize_ffmpeg_location(ffmpeg_location)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        if self.ffmpeg_location:
            logger.info("Using configured FFmpeg location: %s", self.ffmpeg_location)
        else:
            ffmpeg = shutil.which("ffmpeg")
            ffprobe = shutil.which("ffprobe")
            if ffmpeg and ffprobe:
                logger.info("FFmpeg detected | ffmpeg=%s | ffprobe=%s", ffmpeg, ffprobe)
            else:
                logger.warning(
                    "FFmpeg/ffprobe not found in PATH. MP3 conversion will fail until "
                    "FFmpeg is installed or FFMPEG_LOCATION is configured."
                )

    async def download(self, url: str, progress: ProgressCallback | None = None) -> AudioResult:
        return await asyncio.to_thread(self._download_sync, url, progress)

    def _download_sync(self, url: str, progress: ProgressCallback | None) -> AudioResult:
        job_dir = self.base_dir / str(uuid.uuid4())
        job_dir.mkdir(parents=True, exist_ok=False)

        def notify(message: str) -> None:
            if progress:
                try:
                    progress(message)
                except Exception:
                    logger.debug("Progress callback failed", exc_info=True)

        last_stage = ""

        def hook(data: dict[str, Any]) -> None:
            nonlocal last_stage
            status = data.get("status")
            if status == "downloading":
                percent = (data.get("_percent_str") or "").strip()
                speed = (data.get("_speed_str") or "").strip()
                eta = (data.get("_eta_str") or "").strip()
                stage = "Downloading"
                if percent:
                    stage += f" {percent}"
                if speed:
                    stage += f" • {speed}"
                if eta:
                    stage += f" • ETA {eta}"
                # Reduce duplicate callback traffic.
                if stage != last_stage:
                    last_stage = stage
                    notify(stage)
            elif status == "finished":
                notify("Download finished. Converting to MP3…")

        self._ensure_ffmpeg_available()

        output_template = str(job_dir / "%(title).180B [%(id)s].%(ext)s")
        ydl_opts: dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": False,
            "logger": YTDLPLogger(),
            "restrictfilenames": False,
            "writethumbnail": True,
            "prefer_ffmpeg": True,
            "progress_hooks": [hook],
            **({"ffmpeg_location": self.ffmpeg_location} if self.ffmpeg_location else {}),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(self.quality_kbps),
                },
                {"key": "FFmpegMetadata", "add_metadata": True},
                {"key": "FFmpegThumbnailsConvertor", "format": "jpg"},
                {"key": "EmbedThumbnail"},
            ],
            "postprocessor_args": {
                "FFmpegMetadata": ["-id3v2_version", "3"],
            },
        }

        try:
            notify("Reading media information…")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if not info:
                    raise DownloadError("No media information was returned for this URL.")

                # noplaylist=True normally returns a single entry, but unwrap defensively.
                if info.get("_type") == "playlist":
                    entries = [entry for entry in (info.get("entries") or []) if entry]
                    if not entries:
                        raise DownloadError(
                            "This playlist does not contain a downloadable media item."
                        )
                    info = entries[0]

                original_path = Path(ydl.prepare_filename(info))
                expected_mp3 = original_path.with_suffix(".mp3")
                mp3_path = expected_mp3 if expected_mp3.exists() else self._find_mp3(job_dir)

                if mp3_path is None:
                    raise DownloadError(
                        "The media was downloaded, but MP3 conversion did not produce a file."
                    )

                title = first_nonempty(info.get("track"), info.get("title"), default="Audio")
                artist = first_nonempty(
                    info.get("artist"),
                    info.get("creator"),
                    info.get("uploader"),
                    info.get("channel"),
                    default="Unknown",
                )
                source = first_nonempty(
                    info.get("extractor_key"), info.get("extractor"), default="Unknown"
                )
                webpage_url = first_nonempty(
                    info.get("webpage_url"), info.get("original_url"), url, default=url
                )
                duration_raw = info.get("duration")
                duration = int(duration_raw) if isinstance(duration_raw, int | float) else None

                album = self._optional_text(info.get("album"))
                genre = self._optional_text(info.get("genre"))
                if genre is None and isinstance(info.get("categories"), list):
                    categories = [
                        str(item).strip()
                        for item in info["categories"]
                        if str(item).strip()
                    ]
                    if categories:
                        genre = ", ".join(categories[:3])

                upload_date = self._format_upload_date(info.get("upload_date"))
                view_count = self._optional_int(info.get("view_count"))
                like_count = self._optional_int(info.get("like_count"))

                notify("MP3 is ready.")
                return AudioResult(
                    path=mp3_path,
                    title=title,
                    artist=artist,
                    duration=duration,
                    source=source,
                    webpage_url=webpage_url,
                    album=album,
                    genre=genre,
                    upload_date=upload_date,
                    view_count=view_count,
                    like_count=like_count,
                )
        except DownloadError:
            shutil.rmtree(job_dir, ignore_errors=True)
            raise
        except yt_dlp.utils.DownloadError as exc:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.warning("yt-dlp failed for %s: %s", url, exc)
            raise DownloadError(clean_yt_dlp_error(str(exc))) from exc
        except Exception as exc:
            shutil.rmtree(job_dir, ignore_errors=True)
            logger.exception("Unexpected downloader failure for %s", url)
            raise DownloadError(
                "Unexpected download/conversion error. Check the bot logs for details."
            ) from exc

    @staticmethod
    def _optional_text(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _optional_int(value: object) -> int | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, int | float):
            return int(value)
        return None

    @staticmethod
    def _format_upload_date(value: object) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if len(text) == 8 and text.isdigit():
            return f"{text[:4]}-{text[4:6]}-{text[6:8]}"
        return text or None

    @staticmethod
    def _find_mp3(directory: Path) -> Path | None:
        files = sorted(directory.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
        return files[0] if files else None

    @staticmethod
    def _normalize_ffmpeg_location(value: str | None) -> str | None:
        if not value:
            return None
        path = Path(value).expanduser()
        # yt-dlp accepts either a directory or an ffmpeg binary path. For easier
        # ffprobe discovery, normalize an executable path to its containing folder.
        if path.name.lower() in {"ffmpeg", "ffmpeg.exe", "ffprobe", "ffprobe.exe"}:
            path = path.parent
        return str(path.resolve())

    def _ensure_ffmpeg_available(self) -> None:
        if self.ffmpeg_location:
            folder = Path(self.ffmpeg_location)
            ffmpeg_names = ("ffmpeg.exe", "ffmpeg")
            ffprobe_names = ("ffprobe.exe", "ffprobe")
            ffmpeg_ok = any((folder / name).is_file() for name in ffmpeg_names)
            ffprobe_ok = any((folder / name).is_file() for name in ffprobe_names)
            if ffmpeg_ok and ffprobe_ok:
                return
            raise DownloadError(
                "FFmpeg/ffprobe were not found in FFMPEG_LOCATION. "
                "Set it to the folder that contains ffmpeg and ffprobe."
            )

        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            return
        raise DownloadError(
            "FFmpeg and ffprobe are required for MP3 conversion but were not found. "
            "Install FFmpeg, restart the terminal/bot, or set FFMPEG_LOCATION in .env."
        )

    @staticmethod
    def cleanup(result: AudioResult | None) -> None:
        if result is None:
            return
        shutil.rmtree(result.path.parent, ignore_errors=True)
