from bot.utils import clean_yt_dlp_error, first_nonempty, format_duration, human_size, is_valid_http_url


def test_valid_url() -> None:
    assert is_valid_http_url("https://soundcloud.com/example/track")
    assert is_valid_http_url("http://example.com/a")
    assert not is_valid_http_url("example.com/a")
    assert not is_valid_http_url("file:///etc/passwd")


def test_format_duration() -> None:
    assert format_duration(65) == "1:05"
    assert format_duration(3661) == "1:01:01"
    assert format_duration(None) == "Unknown"


def test_human_size() -> None:
    assert human_size(1024) == "1.0 KB"
    assert human_size(1024 * 1024) == "1.0 MB"


def test_first_nonempty() -> None:
    assert first_nonempty("", None, "Artist") == "Artist"
    assert first_nonempty("", default="Unknown") == "Unknown"


def test_clean_yt_dlp_error_strips_ansi_and_maps_known_errors() -> None:
    drm = "\x1b[0;31mERROR:\x1b[0m [soundcloud] 123: This video is DRM protected"
    assert "DRM-protected" in clean_yt_dlp_error(drm)
    assert "\x1b" not in clean_yt_dlp_error(drm)

    ffmpeg = "ERROR: Postprocessing: ffprobe and ffmpeg not found"
    assert "FFmpeg and ffprobe are required" in clean_yt_dlp_error(ffmpeg)
