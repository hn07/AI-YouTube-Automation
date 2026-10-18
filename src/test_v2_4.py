"""Offline V2.4 tests; no FFmpeg process, network, or YouTube is used."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from src.final_video_quality_v2_4 import evaluate_video, save_report, check_video


GOOD_PROBE = {
    "format": {"duration": "42.25", "format_name": "mov,mp4,m4a,3gp,3g2,mj2", "size": "2500000"},
    "streams": [
        {"codec_type": "video", "codec_name": "h264", "width": 1080, "height": 1920},
        {"codec_type": "audio", "codec_name": "aac"}
    ]
}


class V24QualityGateTests(unittest.TestCase):
    def test_valid_video_metadata_passes(self):
        result = evaluate_video("short.mp4", GOOD_PROBE, 2_500_000)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["summary"]["fail_count"], 0)

    def test_missing_audio_fails(self):
        probe = json.loads(json.dumps(GOOD_PROBE))
        probe["streams"] = [probe["streams"][0]]
        result = evaluate_video("short.mp4", probe, 2_500_000)
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(any(x["code"] == "AUDIO_STREAM" and x["status"] == "FAIL" for x in result["findings"]))

    def test_wrong_resolution_fails(self):
        probe = json.loads(json.dumps(GOOD_PROBE))
        probe["streams"][0]["width"] = 1920
        probe["streams"][0]["height"] = 1080
        self.assertEqual(evaluate_video("short.mp4", probe, 2_500_000)["status"], "FAIL")

    def test_wrong_duration_fails(self):
        probe = json.loads(json.dumps(GOOD_PROBE))
        probe["format"]["duration"] = "95.0"
        self.assertEqual(evaluate_video("short.mp4", probe, 2_500_000)["status"], "FAIL")

    def test_non_aac_audio_is_review_not_pass(self):
        probe = json.loads(json.dumps(GOOD_PROBE))
        probe["streams"][1]["codec_name"] = "opus"
        result = evaluate_video("short.mp4", probe, 2_500_000)
        self.assertEqual(result["status"], "REVIEW")

    def test_report_does_not_overwrite_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            video = Path(temp) / "short.mp4"
            video.write_bytes(b"x" * 250_000)
            report = evaluate_video(video, GOOD_PROBE, video.stat().st_size)
            destination = Path(temp) / "report.json"
            destination.write_text('{"original":true}', encoding="utf-8")
            with self.assertRaises(FileExistsError):
                save_report(report, destination)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), {"original": True})

    def test_check_video_uses_ffprobe_json_and_existing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            video = Path(temp) / "short.mp4"
            video.write_bytes(b"x" * 250_000)
            mocked = Mock(returncode=0, stdout=json.dumps(GOOD_PROBE), stderr="")
            with patch("src.final_video_quality_v2_4.find_ffprobe", return_value="ffprobe.exe"), \
                 patch("src.final_video_quality_v2_4.subprocess.run", return_value=mocked):
                result = check_video(video)
            self.assertEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
