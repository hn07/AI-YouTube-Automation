"""Offline tests for V2.2. No source URLs are fetched."""
import json
import tempfile
import unittest
from pathlib import Path

from src.fact_check_v2_2 import evaluate_register, prepare_register


class V22FactCheckTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "output" / "pipeline_jobs").mkdir(parents=True)
        self.job_id = "test_job_002"
        self.script = self.root / "sample.txt"
        self.script.write_text(
            "The ocean contains many different habitats. Scientists study these habitats using ships and instruments. "
            "Some questions remain open because the deep sea is difficult to observe.",
            encoding="utf-8",
        )
        self.job_path = self.root / "output" / "pipeline_jobs" / (self.job_id + ".json")
        self.job_path.write_text(json.dumps({
            "job_id": self.job_id, "topic": "Ocean science",
            "script_path": str(self.script), "stage": "draft_created",
            "human_approved": False, "publish_allowed": False, "history": []
        }), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_prepare_creates_unreviewed_register(self):
        result = prepare_register(self.job_id, root=self.root)
        self.assertGreaterEqual(result["count"], 2)
        self.assertTrue(result["path"].is_file())
        register = json.loads(result["path"].read_text(encoding="utf-8"))
        self.assertTrue(all(c["status"] == "UNREVIEWED" for c in register["claims"]))

    def test_valid_human_review_can_be_recorded(self):
        result = prepare_register(self.job_id, root=self.root)
        register = result["register"]
        register["reviewed_by"] = "Test Reviewer"
        for claim in register["claims"]:
            claim["status"] = "VERIFIED"
            claim["source_urls"] = ["https://example.org/source"]
            claim["reviewer_note"] = "Test fixture only: reviewer states the source supports the claim."
        result["path"].write_text(json.dumps(register), encoding="utf-8")
        report = evaluate_register(self.job_id, str(result["path"]), root=self.root)
        self.assertEqual(report["status"], "HUMAN_REVIEW_COMPLETE")
        self.assertEqual(report["counts"]["VERIFIED"], len(register["claims"]))
        job = json.loads(self.job_path.read_text(encoding="utf-8"))
        self.assertFalse(job["human_approved"])
        self.assertFalse(job["publish_allowed"])

    def test_verified_without_source_is_not_complete(self):
        result = prepare_register(self.job_id, root=self.root)
        register = result["register"]
        register["reviewed_by"] = "Test Reviewer"
        for claim in register["claims"]:
            claim["status"] = "VERIFIED"
            claim["source_urls"] = []
            claim["reviewer_note"] = "Reviewed."
        result["path"].write_text(json.dumps(register), encoding="utf-8")
        report = evaluate_register(self.job_id, str(result["path"]), root=self.root)
        self.assertEqual(report["status"], "NEEDS_HUMAN_REVIEW")
        self.assertTrue(report["findings"])

    def test_existing_register_not_overwritten(self):
        result = prepare_register(self.job_id, root=self.root)
        with self.assertRaises(FileExistsError):
            prepare_register(self.job_id, root=self.root)
        self.assertTrue(result["path"].is_file())


if __name__ == "__main__":
    unittest.main()
