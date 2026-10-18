"""V2.3 gated integration with the existing local Short renderer.

Rendering can contact Microsoft's online Edge TTS endpoint. This module never uploads or publishes.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")
ALLOWED_VOICES = {"en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"}


def _read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object: {}".format(path))
    return value


def _write_json_new(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def _load_and_gate(job_id: str, root: Path) -> tuple[dict, Path, Path]:
    if not JOB_ID_RE.fullmatch(job_id or ""):
        raise ValueError("Invalid job ID.")
    job_path = root / "output" / "pipeline_jobs" / (job_id + ".json")
    if not job_path.is_file():
        raise FileNotFoundError("Job not found: {}".format(job_path))
    job = _read_json(job_path)
    if job.get("job_id") != job_id:
        raise ValueError("Job ID does not match job file.")
    if job.get("human_approved") is not True:
        raise ValueError("Render blocked: record human approval in V2.0 after reviewing the script and fact-check report.")
    if job.get("quality_status") in ("BLOCK", "NOT_RUN", None) or job.get("retention_status") in ("BLOCK", "NOT_RUN", None):
        raise ValueError("Render blocked: V2.0 quality and retention checks must be run and neither may be BLOCK.")
    runs = job.get("v2_2_fact_check_runs")
    if not isinstance(runs, list) or not runs:
        raise ValueError("Render blocked: no V2.2 fact-check evaluation is recorded.")
    latest = runs[-1]
    if latest.get("status") != "HUMAN_REVIEW_COMPLETE":
        raise ValueError("Render blocked: latest V2.2 fact-check status is not HUMAN_REVIEW_COMPLETE.")
    register_path = Path(str(latest.get("register_path") or ""))
    if not register_path.is_absolute():
        register_path = root / register_path
    if not register_path.is_file():
        raise FileNotFoundError("V2.2 claim register not found: {}".format(register_path))
    register = _read_json(register_path)
    if register.get("job_id") != job_id:
        raise ValueError("V2.2 register job_id does not match.")
    if not register.get("claims"):
        raise ValueError("V2.2 claim register is empty.")
    script_value = (job.get("script_path") or "").strip()
    register_script_value = (register.get("script_path") or "").strip()
    if not script_value or not register_script_value:
        raise ValueError("Job and claim register must both record a script_path.")
    job_script = Path(script_value).expanduser()
    if not job_script.is_absolute():
        job_script = root / job_script
    register_script = Path(register_script_value).expanduser()
    if not register_script.is_absolute():
        register_script = root / register_script
    if not job_script.is_file():
        raise FileNotFoundError("Job script not found: {}".format(job_script))
    if job_script.resolve() != register_script.resolve():
        raise ValueError("Render blocked: the approved job script differs from the script recorded in the V2.2 claim register. Review the current script and create/evaluate a fresh register.")
    return job, job_path, job_script


def render_approved_job(job_id: str, confirm_render: bool = False, voice: str = "en-US-AriaNeural",
                        root: Optional[Path] = None, render_func: Optional[Callable] = None) -> dict:
    root = Path(root or ROOT).resolve()
    if not confirm_render:
        raise ValueError("Rendering requires explicit confirmation (--confirm-render).")
    if voice not in ALLOWED_VOICES:
        raise ValueError("Unsupported voice. Choose one of: {}".format(", ".join(sorted(ALLOWED_VOICES))))
    job, job_path, script_path = _load_and_gate(job_id, root)
    script = script_path.read_text(encoding="utf-8-sig").strip()
    if len(script.split()) < 60:
        raise ValueError("Render blocked: narration must contain at least 60 words. Review the script manually.")
    title = (job.get("title") or job.get("topic") or "YouTube Short").strip()
    if not title:
        raise ValueError("Job title/topic is empty.")
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / "output" / "rendered_jobs" / (job_id + "_" + stamp)
    if output_dir.exists():
        raise FileExistsError("Output directory already exists; refusing to overwrite: {}".format(output_dir))
    output_dir.mkdir(parents=True, exist_ok=False)
    if render_func is None:
        src_dir = str(root / "src")
        if src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        from video_maker import render_short
        render_func = render_short
    mp4, duration = render_func(title, script, output_dir, voice)
    mp4 = Path(mp4)
    if not mp4.is_file() or mp4.stat().st_size <= 0:
        raise RuntimeError("Renderer returned without a valid MP4 file.")
    rendered_at = datetime.now(timezone.utc).isoformat()
    artifact = {
        "schema_version": "2.3",
        "job_id": job_id,
        "rendered_at_utc": rendered_at,
        "script_path": str(script_path),
        "video_path": str(mp4.resolve()),
        "duration_seconds": round(float(duration), 2),
        "file_size_bytes": mp4.stat().st_size,
        "voice": voice,
        "status": "RENDERED_NEEDS_FINAL_HUMAN_REVIEW",
        "upload_allowed": False,
        "limitations": [
            "Rendering does not upload, schedule, or publish the video.",
            "Voice generation uses the existing edge-tts integration and requires Internet access.",
            "Review the full MP4, narration, captions, source accuracy, media rights, and platform policy before any separate upload workflow."
        ]
    }
    _write_json_new(output_dir / "render_manifest.json", artifact)
    job.setdefault("v2_3_render_runs", []).append({
        "rendered_at_utc": rendered_at,
        "status": artifact["status"],
        "video_path": artifact["video_path"],
        "manifest_path": str(output_dir / "render_manifest.json"),
        "duration_seconds": artifact["duration_seconds"],
        "upload_allowed": False
    })
    job["stage"] = "rendered_needs_human_review"
    job["publish_allowed"] = False
    job.setdefault("history", []).append({
        "at_utc": rendered_at,
        "event": "V2_3_RENDER_COMPLETED",
        "detail": "MP4 rendered; final video review required; upload/publishing remains disabled."
    })
    temp_job = job_path.with_name(job_path.name + ".v2_3.tmp")
    with temp_job.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(job, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    temp_job.replace(job_path)
    return artifact


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.3 render an approved and fact-check-reviewed job. No upload.")
    parser.add_argument("job_id")
    parser.add_argument("--confirm-render", action="store_true", help="Explicitly authorize local rendering and online TTS request.")
    parser.add_argument("--voice", default="en-US-AriaNeural", choices=sorted(ALLOWED_VOICES))
    args = parser.parse_args(argv)
    try:
        result = render_approved_job(args.job_id, args.confirm_render, args.voice)
        print("V2.3 RENDER STATUS: {}".format(result["status"]))
        print("Video: {}".format(result["video_path"]))
        print("Duration: {:.2f}s | Size: {} bytes".format(result["duration_seconds"], result["file_size_bytes"]))
        print("Manifest: {}".format(Path(result["video_path"]).parent / "render_manifest.json"))
        print("Final human video review is required. No upload or publishing was performed.")
        return 0
    except (OSError, UnicodeError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print("ERROR: {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
