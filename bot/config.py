from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True, slots=True)
class Settings:
    bot_token: str
    download_dir: Path
    log_dir: Path
    max_concurrent_downloads: int
    telegram_max_file_mb: int
    mp3_quality_kbps: int
    ffmpeg_location: str | None

    @classmethod
    def from_env(cls) -> Settings:
        token = os.getenv("BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "BOT_TOKEN is missing. Copy .env.example to .env and set your token."
            )

        return cls(
            bot_token=token,
            download_dir=Path(os.getenv("DOWNLOAD_DIR", "downloads")).resolve(),
            log_dir=Path(os.getenv("LOG_DIR", "logs")).resolve(),
            max_concurrent_downloads=max(1, int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))),
            telegram_max_file_mb=max(1, int(os.getenv("TELEGRAM_MAX_FILE_MB", "50"))),
            mp3_quality_kbps=320,
            ffmpeg_location=os.getenv("FFMPEG_LOCATION", "").strip() or None,
        )
