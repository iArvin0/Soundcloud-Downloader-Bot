from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlparse


def is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def format_duration(seconds: int | float | None) -> str:
    if seconds is None:
        return "Unknown"

    total = max(0, int(seconds))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def human_size(num_bytes: int) -> str:
    size = float(max(0, num_bytes))
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def first_nonempty(*values: object, default: str = "Unknown") -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value).strip()
    return default


def safe_unlink(path: Path | None) -> None:
    if path is None:
        return
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def clean_yt_dlp_error(message: str) -> str:
    """Convert noisy yt-dlp errors into concise user-facing text."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    cleaned = ansi_escape.sub("", message).replace("ERROR:", "").strip()
    lowered = cleaned.lower()

    if "drm protected" in lowered or "drm-protected" in lowered:
        return (
            "This media is DRM-protected, so yt-dlp cannot download it. "
            "This bot does not bypass DRM or access controls."
        )

    if "ffprobe and ffmpeg not found" in lowered or "ffmpeg not found" in lowered:
        return (
            "FFmpeg and ffprobe are required for MP3 conversion but were not found. "
            "Install FFmpeg, restart the bot, or set FFMPEG_LOCATION in .env."
        )

    if len(cleaned) > 450:
        cleaned = cleaned[:447] + "…"
    return cleaned or "yt-dlp could not download this URL."
