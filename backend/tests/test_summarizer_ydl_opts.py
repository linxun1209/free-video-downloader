import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

sys.modules.setdefault("httpx", SimpleNamespace(get=None))
sys.modules.setdefault("yt_dlp", SimpleNamespace(YoutubeDL=None))
sys.modules.setdefault("openai", SimpleNamespace(OpenAI=object))

import summarizer


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

    def download(self, urls):
        return None


class SubtitleExtractorYdlOptsTests(unittest.TestCase):
    def setUp(self):
        _DummyYDL.last_opts = None
        _DummyYDL.info_to_return = {
            "id": "7064781119429807363",
            "title": "demo",
            "subtitles": {},
            "automatic_captions": {},
        }
        _DummyYDL.error_to_raise = None

    def test_get_video_info_applies_cookiefile_from_env(self):
        extractor = summarizer.SubtitleExtractor()

        with patch.object(summarizer.yt_dlp, "YoutubeDL", _DummyYDL):
            with patch.dict(os.environ, {"YTDLP_COOKIEFILE": "/tmp/douyin.cookies"}, clear=False):
                extractor._get_video_info("https://www.douyin.com/video/7064781119429807363")

        self.assertEqual(_DummyYDL.last_opts["cookiefile"], "/tmp/douyin.cookies")
        self.assertTrue(_DummyYDL.last_opts["skip_download"])
        self.assertTrue(_DummyYDL.last_opts["writesubtitles"])
        self.assertTrue(_DummyYDL.last_opts["writeautomaticsub"])

    def test_get_video_info_rewrites_douyin_fresh_cookies_error(self):
        extractor = summarizer.SubtitleExtractor()
        _DummyYDL.error_to_raise = Exception(
            "\x1b[0;31mERROR:\x1b[0m [Douyin] 7064781119429807363: Fresh cookies (not necessarily logged in) are needed"
        )

        with patch.object(summarizer.yt_dlp, "YoutubeDL", _DummyYDL):
            with self.assertRaises(ValueError) as ctx:
                extractor._get_video_info("https://www.douyin.com/video/7064781119429807363")

        self.assertIn("抖音当前要求提供新鲜 cookies", str(ctx.exception))
        self.assertIn("YTDLP_COOKIEFILE", str(ctx.exception))
        self.assertNotIn("\x1b", str(ctx.exception))

    def test_download_and_parse_applies_cookiefile_from_env(self):
        extractor = summarizer.SubtitleExtractor()

        with patch.object(summarizer.yt_dlp, "YoutubeDL", _DummyYDL):
            with patch.dict(os.environ, {"YTDLP_COOKIEFILE": "/tmp/douyin.cookies"}, clear=False):
                segments = extractor._download_and_parse(
                    "https://www.douyin.com/video/7064781119429807363",
                    "zh",
                    "auto",
                )

        self.assertEqual(segments, [])
        self.assertEqual(_DummyYDL.last_opts["cookiefile"], "/tmp/douyin.cookies")
        self.assertEqual(_DummyYDL.last_opts["subtitleslangs"], ["zh"])
        self.assertEqual(_DummyYDL.last_opts["subtitlesformat"], "vtt")


if __name__ == "__main__":
    unittest.main()
