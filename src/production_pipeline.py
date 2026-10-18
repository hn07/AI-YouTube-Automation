"""V2.0 safe local YouTube production pipeline; offline, no rendering or uploading."""
from __future__ import annotations
import argparse, json, re, sys, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).resolve().parents[1]
JOBS_DIR = ROOT / "output" / "pipeline_jobs"
JOB_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,79}$")

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

def safe_job_path(job_id: str, jobs_dir: Optional[Path] = None) -> Path:
    if not JOB_ID_RE.fullmatch(job_id):
        raise ValueError("Invalid job ID. Use 3-80 letters, numbers, '_' or '-'.")
    return (jobs_dir or JOBS_DIR) / (job_id + ".json")

def _atomic_write(path: Path, payload: Dict[str, Any], exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise FileExistsError("Job/report already exists; refusing to overwrite: {}".format(path))
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        if exclusive and path.exists():
            raise FileExistsError("Job/report already exists; refusing to overwrite: {}".format(path))
        temp.replace(path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass

def create_job(topic: str, title: str = "", description: str = "", source_url: str = "",
               target_seconds: int = 45, script_path: str = "",
               jobs_dir: Optional[Path] = None) -> Dict[str, Any]:
    topic = (topic or "").strip()
    if not topic:
        raise ValueError("Topic cannot be empty.")
    if not 10 <= int(target_seconds) <= 180:
        raise ValueError("Target duration must be between 10 and 180 seconds.")
    job_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    path = safe_job_path(job_id, jobs_dir)
    stamp = now_utc()
    job = {
        "schema_version": "2.0", "job_id": job_id, "created_at_utc": stamp, "updated_at_utc": stamp,
        "topic": topic, "source_url": (source_url or "").strip(), "title": (title or "").strip(),
        "description": (description or "").strip(), "target_seconds": int(target_seconds),
        "script_path": (script_path or "").strip(), "stage": "topic_selected",
        "quality_status": "NOT_RUN", "retention_status": "NOT_RUN", "human_approved": False,
        "approval_note": "", "publish_allowed": False,
        "history": [{"at_utc": stamp, "event": "JOB_CREATED", "detail": "Local job created; no network or upload performed."}],
        "limitations": ["No automatic research or fact-checking.", "Quality and retention checks are heuristic.",
                        "Human approval does not upload or publish a video."]
    }
    _atomic_write(path, job, exclusive=True)
    job["job_file"] = str(path)
    return job

def load_job(job_id: str, jobs_dir: Optional[Path] = None) -> Dict[str, Any]:
    path = safe_job_path(job_id, jobs_dir)
    if not path.is_file():
        raise FileNotFoundError("Job not found: {}".format(path))
    with path.open("r", encoding="utf-8-sig") as stream:
        job = json.load(stream)
    if job.get("job_id") != job_id:
        raise ValueError("Job ID does not match the requested file.")
    return job

def save_job(job: Dict[str, Any], jobs_dir: Optional[Path] = None) -> Path:
    path = safe_job_path(str(job.get("job_id", "")), jobs_dir)
    job["updated_at_utc"] = now_utc()
    _atomic_write(path, job)
    return path

def validate_job(job_id: str, jobs_dir: Optional[Path] = None) -> Dict[str, Any]:
    job = load_job(job_id, jobs_dir)
    script_value = (job.get("script_path") or "").strip()
    if not script_value:
        raise ValueError("No script path set. Edit the job JSON and set script_path to a UTF-8 .txt file.")
    script_path = Path(script_value).expanduser()
    if not script_path.is_absolute():
        script_path = ROOT / script_path
    if not script_path.is_file():
        raise FileNotFoundError("Script file not found: {}".format(script_path))
    script = script_path.read_text(encoding="utf-8-sig")
    src_dir = str(ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    from content_quality import check_content
    from retention_review import analyze_retention
    quality = check_content(script, job.get("title", ""), job.get("description", ""))
    retention = analyze_retention(script, int(job.get("target_seconds", 45)))
    reports_dir = ROOT / "output" / "pipeline_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    quality_path = reports_dir / (job_id + "_quality.json")
    retention_path = reports_dir / (job_id + "_retention.json")
    for report_path, data in ((quality_path, quality), (retention_path, retention)):
        if report_path.exists():
            raise FileExistsError("Report already exists; archive it before rerunning: {}".format(report_path))
        _atomic_write(report_path, data, exclusive=True)
    job["script_path"] = str(script_path)
    job["quality_status"], job["retention_status"] = quality["status"], retention["status"]
    job["human_approved"], job["approval_note"], job["publish_allowed"] = False, "", False
    job["stage"] = "blocked" if "BLOCK" in (quality["status"], retention["status"]) else "needs_human_review"
    job.setdefault("history", []).append({"at_utc": now_utc(), "event": "CHECKS_COMPLETED",
        "detail": "Quality={}; retention={}; human review remains required.".format(quality["status"], retention["status"])})
    job["reports"] = {"quality": str(quality_path), "retention": str(retention_path)}
    save_job(job, jobs_dir)
    return {"job": job, "quality": quality, "retention": retention}

def approve_job(job_id: str, note: str, jobs_dir: Optional[Path] = None) -> Dict[str, Any]:
    job = load_job(job_id, jobs_dir)
    if job.get("stage") == "blocked" or job.get("quality_status") in ("BLOCK", "NOT_RUN") or job.get("retention_status") in ("BLOCK", "NOT_RUN"):
        raise ValueError("Cannot approve: checks must be completed and neither check may be BLOCK.")
    if not (note or "").strip():
        raise ValueError("An approval note is required.")
    job["human_approved"], job["approval_note"], job["stage"] = True, note.strip(), "human_approved"
    job["publish_allowed"] = False
    job.setdefault("history", []).append({"at_utc": now_utc(), "event": "HUMAN_APPROVED",
        "detail": note.strip() + " Upload/publishing remains disabled in V2.0."})
    save_job(job, jobs_dir)
    return job

def list_jobs(jobs_dir: Optional[Path] = None):
    directory = jobs_dir or JOBS_DIR
    if not directory.exists():
        return []
    jobs = []
    for path in sorted(directory.glob("*.json"), reverse=True):
        try:
            with path.open("r", encoding="utf-8-sig") as stream:
                item = json.load(stream)
            jobs.append({"job_id": item.get("job_id", path.stem), "stage": item.get("stage", "unknown"),
                "topic": item.get("topic", ""), "quality_status": item.get("quality_status", "NOT_RUN"),
                "retention_status": item.get("retention_status", "NOT_RUN"),
                "human_approved": bool(item.get("human_approved", False))})
        except (OSError, ValueError):
            jobs.append({"job_id": path.stem, "stage": "invalid_json", "topic": "",
                "quality_status": "UNKNOWN", "retention_status": "UNKNOWN", "human_approved": False})
    return jobs

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.0 local YouTube production pipeline; no upload.")
    sub = parser.add_subparsers(dest="command", required=True)
    new = sub.add_parser("new", help="Create a production job.")
    new.add_argument("--topic", required=True); new.add_argument("--title", default="")
    new.add_argument("--description", default=""); new.add_argument("--source-url", default="")
    new.add_argument("--target-seconds", type=int, default=45); new.add_argument("--script-path", default="")
    check = sub.add_parser("check", help="Run V1.8 quality and V1.9 retention checks."); check.add_argument("job_id")
    approve = sub.add_parser("approve", help="Record human review; does not publish.")
    approve.add_argument("job_id"); approve.add_argument("--note", required=True)
    sub.add_parser("list", help="List known jobs.")
    args = parser.parse_args(argv)
    try:
        if args.command == "new":
            job = create_job(args.topic, args.title, args.description, args.source_url, args.target_seconds, args.script_path)
            print("JOB CREATED: {}".format(job["job_id"])); print("File: {}".format(job["job_file"]))
            print("Edit the job JSON to set description and script_path, then run check.")
        elif args.command == "check":
            result = validate_job(args.job_id)
            print("JOB: {} | STAGE: {}".format(args.job_id, result["job"]["stage"]))
            print("QUALITY: {} | RETENTION: {}".format(result["quality"]["status"], result["retention"]["status"]))
            print("Quality report: {}".format(result["job"]["reports"]["quality"]))
            print("Retention report: {}".format(result["job"]["reports"]["retention"]))
            print("Human review and fact-checking are required. Nothing was uploaded.")
        elif args.command == "approve":
            job = approve_job(args.job_id, args.note)
            print("HUMAN APPROVAL RECORDED: {}".format(job["job_id"]))
            print("Upload/publishing remains disabled in V2.0.")
        else:
            jobs = list_jobs()
            if not jobs: print("No jobs yet.")
            for item in jobs:
                print("{job_id} | {stage} | Q={quality_status} | R={retention_status} | approved={human_approved} | {topic}".format(**item))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError) as exc:
        print("ERROR: {}".format(exc)); return 2

if __name__ == "__main__":
    raise SystemExit(main())
