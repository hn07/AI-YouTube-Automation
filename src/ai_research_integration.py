"""V2.1 safe AI-script and RSS-research integration; no rendering or publishing."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
JOB_ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,79}$")


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        temp.replace(path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def _load_job(job_id: str, root: Path) -> tuple[dict, Path]:
    if not JOB_ID_RE.fullmatch(job_id or ""):
        raise ValueError("Invalid job ID.")
    path = root / "output" / "pipeline_jobs" / (job_id + ".json")
    if not path.is_file():
        raise FileNotFoundError("Job not found: {}".format(path))
    with path.open("r", encoding="utf-8-sig") as stream:
        job = json.load(stream)
    if job.get("job_id") != job_id:
        raise ValueError("Job ID does not match the job file.")
    return job, path


def _local_script(topic: str, style: str) -> str:
    topic = re.sub(r"\s+", " ", (topic or "").strip())[:180]
    if not topic:
        raise ValueError("Topic cannot be empty.")
    if style == "story":
        lines = [
            "What is the most surprising question about {}?".format(topic),
            "Start with what can be checked, not with the scariest claim.",
            "Separate established evidence from theories, rumors, and unanswered questions.",
            "Look for primary sources and compare them with independent, reputable explanations.",
            "The details that remain uncertain can be interesting, but uncertainty is not proof.",
            "What would you want researchers to investigate next?"
        ]
    else:
        lines = [
            "What is the most surprising thing we can responsibly ask about {}?".format(topic),
            "The first headline you see may leave out important context.",
            "Look for the original evidence, then compare it with independent, reputable sources.",
            "Separate what is known from what scientists or researchers are still investigating.",
            "Avoid treating a theory, rumor, or dramatic claim as an established fact.",
            "What question about this topic would you like to explore next?"
        ]
    return "\n\n".join(lines)


def _generate_script(topic: str, style: str, provider: str) -> tuple[str, str]:
    if provider == "local":
        return _local_script(topic, style), "local-template"
    src_dir = str(ROOT / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    try:
        from ai_script_provider import generate
    except ImportError as exc:
        raise RuntimeError("Cannot load src/ai_script_provider.py: {}".format(exc))
    if not (os.getenv("AI_API_BASE_URL", "").strip() and
            os.getenv("AI_API_KEY", "").strip() and os.getenv("AI_MODEL", "").strip()):
        raise RuntimeError("AI provider is not configured. Set AI_API_BASE_URL, AI_API_KEY, and AI_MODEL in your environment/.env.")
    script = generate(topic, style)
    if not script:
        raise RuntimeError("AI provider returned no script.")
    return script.strip(), "configured-ai-provider"


def draft_for_job(job_id: str, topic: str = "", title: str = "", description: str = "",
                  source_url: str = "", style: str = "curiosity", provider: str = "local",
                  root: Optional[Path] = None) -> dict:
    root = Path(root or ROOT).resolve()
    job, job_path = _load_job(job_id, root)
    topic = (topic or job.get("topic") or "").strip()
    if not topic:
        raise ValueError("Topic is empty; pass --topic or set topic in the job.")
    script, provider_used = _generate_script(topic, style, provider)
    scripts_dir = root / "output" / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / (job_id + "_v2_1_draft.txt")
    if script_path.exists():
        raise FileExistsError("Draft already exists; refusing to overwrite: {}".format(script_path))
    # Exclusive create prevents overwriting an existing user file.
    with script_path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(script.strip() + "\n")

    job["topic"] = topic
    if title.strip():
        job["title"] = title.strip()
    elif not (job.get("title") or "").strip():
        job["title"] = topic
    if description.strip():
        job["description"] = description.strip()
    if source_url.strip():
        if not source_url.lower().startswith("https://"):
            script_path.unlink(missing_ok=True)
            raise ValueError("Source URL must begin with https://.")
        job["source_url"] = source_url.strip()
    # Preserve a user's existing script_path unless it was empty.
    previous_script = (job.get("script_path") or "").strip()
    if not previous_script:
        job["script_path"] = str(script_path)
    job["v2_1_draft"] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "provider": provider_used,
        "path": str(script_path),
        "review_status": "NOT_REVIEWED",
        "note": "Draft only. Verify factual claims and sources; no video was rendered or uploaded."
    }
    job["stage"] = "draft_created"
    job.setdefault("history", []).append({
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "event": "V2_1_SCRIPT_DRAFT_CREATED",
        "detail": "Provider={}; draft={}; no rendering/upload/publishing.".format(provider_used, script_path)
    })
    try:
        _atomic_json(job_path, job)
    except Exception:
        # Keep the script for recovery; never silently delete a generated artifact.
        raise
    return {"job": job, "script_path": script_path, "provider": provider_used,
            "job_script_path_updated": not bool(previous_script)}


def discover_topics(limit: int = 10, root: Optional[Path] = None) -> dict:
    """Run the existing optional RSS discovery and save candidates under the chosen root."""
    root = Path(root or ROOT).resolve()
    src_dir = str(root / "src")
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    try:
        import topic_research
    except ImportError as exc:
        raise RuntimeError("Cannot load src/topic_research.py: {}".format(exc))
    items = topic_research.discover_topics(limit=max(1, min(int(limit), 100)))
    # Existing V1.6 research module writes to project ROOT. Copy its output into the requested root
    # only when that is a test root; production root is already correct.
    candidate_path = root / "output" / "researched_topic_candidates.json"
    if root != ROOT:
        source_path = topic_research.CANDIDATES
        if source_path.is_file():
            candidate_path.parent.mkdir(parents=True, exist_ok=True)
            candidate_path.write_text(source_path.read_text(encoding="utf-8"), encoding="utf-8")
    return {"count": len(items), "items": items, "path": str(candidate_path)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.1 script and research helper. No publishing.")
    sub = parser.add_subparsers(dest="command", required=True)
    research = sub.add_parser("research", help="Fetch optional RSS topic leads for human review.")
    research.add_argument("--limit", type=int, default=10)
    draft = sub.add_parser("draft", help="Create a non-overwriting script draft for an existing V2.0 job.")
    draft.add_argument("job_id")
    draft.add_argument("--topic", default="")
    draft.add_argument("--title", default="")
    draft.add_argument("--description", default="")
    draft.add_argument("--source-url", default="")
    draft.add_argument("--style", choices=("curiosity", "story"), default="curiosity")
    draft.add_argument("--provider", choices=("local", "ai"), default="local")
    args = parser.parse_args(argv)
    try:
        if args.command == "research":
            result = discover_topics(args.limit)
            print("RESEARCH LEADS: {}".format(result["count"]))
            print("Saved: {}".format(result["path"]))
            for index, item in enumerate(result["items"], 1):
                print("{}. {}".format(index, item.get("topic", "")))
                print("   Source: {}".format(item.get("source_url", "")))
            print("Important: RSS items are leads only, not fact-checked.")
        else:
            result = draft_for_job(args.job_id, args.topic, args.title, args.description,
                                   args.source_url, args.style, args.provider)
            print("DRAFT CREATED: {}".format(result["script_path"]))
            print("Provider: {}".format(result["provider"]))
            print("Job file: {}".format(result["job"]["job_id"]))
            if result["job_script_path_updated"]:
                print("Job script_path set to the new draft.")
            else:
                print("Existing job script_path was preserved: {}".format(result["job"].get("script_path")))
                print("Review the new draft, then manually choose whether to update script_path.")
            print("Draft needs human review and fact-checking. Nothing was rendered or uploaded.")
        return 0
    except (OSError, UnicodeError, ValueError, RuntimeError, KeyError) as exc:
        print("ERROR: {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
