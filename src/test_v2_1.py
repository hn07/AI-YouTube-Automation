"""Offline unit tests for V2.1; no network or AI API is used."""
import json
import tempfile
import unittest
from pathlib import Path

from src.ai_research_integration import draft_for_job


class V21DraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.jobs = self.root / "output" / "pipeline_jobs"
        self.jobs.mkdir(parents=True)
        self.job_id = "test_job_001"
        self.job_path = self.jobs / (self.job_id + ".json")
        self.job = {
            "schema_version": "2.0",
            "job_id": self.job_id,
            "topic": "Creepy Facts About the Ocean",
            "title": "Creepy Facts About the Ocean",
            "description": "",
            "source_url": "",
            "script_path": "D:/keep-existing-script.txt",
            "stage": "topic_selected",
            "history": [],
        }
        self.job_path.write_text(json.dumps(self.job), encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def test_local_draft_created_without_overwriting_existing_script_path(self):
        result = draft_for_job(self.job_id, provider="local", root=self.root)
        self.assertTrue(result["script_path"].is_file())
        self.assertIn("What is the most surprising", result["script_path"].read_text(encoding="utf-8"))
        saved = json.loads(self.job_path.read_text(encoding="utf-8"))
        self.assertEqual(saved["script_path"], "D:/keep-existing-script.txt")
        self.assertEqual(saved["stage"], "draft_created")
        self.assertEqual(saved["v2_1_draft"]["review_status"], "NOT_REVIEWED")

    def test_existing_draft_is_never_overwritten(self):
        destination = self.root / "output" / "scripts" / (self.job_id + "_v2_1_draft.txt")
        destination.parent.mkdir(parents=True)
        destination.write_text("KEEP ME", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            draft_for_job(self.job_id, provider="local", root=self.root)
        self.assertEqual(destination.read_text(encoding="utf-8"), "KEEP ME")

    def test_empty_topic_is_rejected(self):
        saved = json.loads(self.job_path.read_text(encoding="utf-8"))
        saved["topic"] = ""
        self.job_path.write_text(json.dumps(saved), encoding="utf-8")
        with self.assertRaises(ValueError):
            draft_for_job(self.job_id, provider="local", root=self.root)


if __name__ == "__main__":
    unittest.main()
