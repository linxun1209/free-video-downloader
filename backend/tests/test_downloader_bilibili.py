import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import downloader


class _DummyYDL:
    last_opts = None
    info_to_return = None
    error_to_raise = None

    def __init__(self, opts):
        _DummyYDL.last_opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download=False):
        if _DummyYDL.error_to_raise is not None:
            raise _DummyYDL.error_to_raise
        return _DummyYDL.info_to_return


@pytest.fixture(autouse=True)
def _reset_dummy():
    _DummyYDL.last_opts = None
    _DummyYDL.info_to_return = None
    _DummyYDL.error_to_raise = None


def test_parse_video_uses_bilibili_browser_headers(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _DummyYDL)
    _DummyYDL.info_to_return = {
        "id": "BV1xx411c7mD",
        "title": "demo",
        "thumbnail": "",
        "duration": 10,
        "uploader": "tester",
        "extractor": "BiliBili",
        "formats": [],
        "subtitles": {},
        "automatic_captions": {},
    }

    instance = downloader.VideoDownloader()
    instance.parse_video("https://www.bilibili.com/video/BV1xx411c7mD")

    headers = _DummyYDL.last_opts["http_headers"]
    assert headers["Referer"] == "https://www.bilibili.com/"
    assert "Mozilla/5.0" in headers["User-Agent"]
    assert _DummyYDL.last_opts["noplaylist"] is True


def test_parse_video_rewrites_bilibili_412_to_friendly_message(monkeypatch):
    monkeypatch.setattr(downloader.yt_dlp, "YoutubeDL", _DummyYDL)
    _DummyYDL.error_to_raise = Exception(
        "\x1b[0;31mERROR:\x1b[0m [BiliBili] abc123: Unable to download webpage: HTTP Error 412: Precondition Failed"
    )

    instance = downloader.VideoDownloader()

    with pytest.raises(ValueError) as exc:
        instance.parse_video("https://www.bilibili.com/video/BV1xx411c7mD")

    assert "B 站返回了 412" in str(exc.value)
    assert "\x1b" not in str(exc.value)
