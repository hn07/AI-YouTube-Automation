"""V2.3 tests use a fake renderer; no TTS, FFmpeg, or network calls."""
import json
import tempfile
import unittest
from pathlib import Path

from src.render_pipeline_v2_3 import render_approved_job


class V23RenderingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.job_id = "test_render_003"
        self.jobs = self.root / "output" / "pipeline_jobs"
        self.jobs.mkdir(parents=True)
        self.scripts = self.root / "output" / "scripts"
        self.scripts.mkdir(parents=True)
        self.script = self.scripts / "approved.txt"
        self.script.write_text(
            "Imagine exploring the ocean. Scientists use many tools to study the sea. "
            "Some regions are difficult to observe directly. Researchers compare measurements, "
            "photographs, and samples to understand what lives there. The details vary by depth, "
            "location, and conditions. Always check reliable sources before repeating a specific claim. "
            "The most interesting discoveries often lead to new questions, careful experiments, and better explanations that can be shared with curious viewers.",
            encoding="utf-8",
        )
        self.register_path = self.root / "output" / "fact_check" / (self.job_id + "_claims.json")
        self.register_path.parent.mkdir(parents=True)
        self.register_path.write_text(json.dumps({
            "job_id": self.job_id, "script_path": str(self.script),
            "reviewed_by": "Test reviewer",
            "claims": [{"claim_id": "C001", "status": "VERIFIED",
                        "source_urls": ["https://example.org/source"],
                        "reviewer_note": "Test fixture only"}]
        }), encoding="utf-8")
        self.job_path = self.jobs / (self.job_id + ".json")
        self.job_path.write_text(json.dumps({
            "job_id": self.job_id, "topic": "Ocean facts", "title": "Ocean facts",
            "script_path": str(self.script), "quality_status": "REVIEW",
            "retention_status": "REVIEW", "human_approved": True,
            "publish_allowed": False, "stage": "human_approved", "history": [],
            "v2_2_fact_check_runs": [{
                "status": "HUMAN_REVIEW_COMPLETE", "register_path": str(self.register_path)
            }]
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def fake_renderer(self, title, script, output_dir, voice):
        path = output_dir / "short.mp4"
        path.write_bytes(b"FAKE-MP4-FOR-TEST")
        return path, 42.0

    def test_gate_blocks_without_explicit_render_confirmation(self):
        with self.assertRaisesRegex(ValueError, "explicit confirmation"):
            render_approved_job(self.job_id, root=self.root, render_func=self.fake_renderer)

    def test_gate_blocks_unapproved_job(self):
        job = json.loads(self.job_path.read_text(encoding="utf-8"))
        job["human_approved"] = False
        self.job_path.write_text(json.dumps(job), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "human approval"):
            render_approved_job(self.job_id, True, root=self.root, render_func=self.fake_renderer)

    def test_gate_blocks_stale_script_mismatch(self):
        changed = self.root / "changed.txt"
        changed.write_text(self.script.read_text(encoding="utf-8"), encoding="utf-8")
        job = json.loads(self.job_path.read_text(encoding="utf-8"))
        job["script_path"] = str(changed)
        self.job_path.write_text(json.dumps(job), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from the script"):
            render_approved_job(self.job_id, True, root=self.root, render_func=self.fake_renderer)

    def test_fake_render_creates_manifest_and_never_enables_upload(self):
        result = render_approved_job(self.job_id, True, root=self.root, render_func=self.fake_renderer)
        self.assertEqual(result["status"], "RENDERED_NEEDS_FINAL_HUMAN_REVIEW")
        self.assertFalse(result["upload_allowed"])
        self.assertTrue(Path(result["video_path"]).is_file())
        manifest = json.loads((Path(result["video_path"]).parent / "render_manifest.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["upload_allowed"])
        saved = json.loads(self.job_path.read_text(encoding="utf-8"))
        self.assertFalse(saved["publish_allowed"])
        self.assertEqual(saved["stage"], "rendered_needs_human_review")


if __name__ == "__main__":
    unittest.main()
