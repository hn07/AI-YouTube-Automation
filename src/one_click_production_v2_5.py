"""V2.5 one-command safe production orchestrator.

This orchestrator does not invent fact-check results, approve a job, overwrite reports,
or upload/publish. It runs only the existing gates and renders only when all required
review gates have already passed.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JOB_DIR = ROOT / "output" / "pipeline_jobs"
REPORT_DIR = ROOT / "output" / "v2_5_runs"


def read_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object: {}".format(path))
    return data


def write_new(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run_step(label: str, args: list[str]) -> dict:
    result = subprocess.run(args, cwd=str(ROOT), capture_output=True, text=True, check=False)
    return {
        "step": label,
        "command": args,
        "return_code": result.returncode,
        "stdout": (result.stdout or "")[-12000:],
        "stderr": (result.stderr or "")[-6000:],
        "status": "PASS" if result.returncode == 0 else "BLOCKED",
    }


def run_production(job_id: str, voice: str = "en-US-AriaNeural") -> dict:
    if not job_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in job_id):
        raise ValueError("Invalid job ID.")
    job_path = JOB_DIR / (job_id + ".json")
    if not job_path.is_file():
        raise FileNotFoundError("Job not found: {}".format(job_path))
    job = read_json(job_path)
    if job.get("job_id") != job_id:
        raise ValueError("Job ID mismatch in job JSON.")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / (job_id + "_v2_5_" + stamp + ".json")
    steps: list[dict] = []
    blockers: list[str] = []
    script_value = (job.get("script_path") or "").strip()
    script = Path(script_value).expanduser() if script_value else None
    if script is not None and not script.is_absolute():
        script = ROOT / script
    if script is None or not script.is_file():
        blockers.append("Script file is missing. Add a valid script_path to the job.")
    else:
        try:
            words = len(script.read_text(encoding="utf-8-sig").split())
            if words < 60:
                blockers.append("Script has {} words; V2.3 requires at least 60.".format(words))
        except (OSError, UnicodeError) as exc:
            blockers.append("Could not read script: {}".format(exc))

    # Existing quality/retention checks must already have run and remain non-blocking.
    if job.get("quality_status") in (None, "", "NOT_RUN", "BLOCK"):
        blockers.append("V2.0 content quality gate has not passed; run the existing check and review its report.")
    if job.get("retention_status") in (None, "", "NOT_RUN", "BLOCK"):
        blockers.append("V2.0 retention gate has not passed; run the existing check and review its report.")

    if job.get("human_approved") is not True:
        blockers.append("Human approval is not recorded. V2.5 will not create or simulate approval.")

    runs = job.get("v2_2_fact_check_runs")
    if not isinstance(runs, list) or not runs:
        blockers.append("No V2.2 fact-check evaluation is recorded.")
        register = None
    else:
        latest = runs[-1]
        if latest.get("status") != "HUMAN_REVIEW_COMPLETE":
            blockers.append("Latest V2.2 fact-check status is not HUMAN_REVIEW_COMPLETE.")
        reg_value = str(latest.get("register_path") or "")
        register_path = Path(reg_value).expanduser() if reg_value else None
        if register_path is not None and not register_path.is_absolute():
            register_path = ROOT / register_path
        if register_path is None or not register_path.is_file():
            blockers.append("The latest V2.2 claim register is missing.")
            register = None
        else:
            try:
                register = read_json(register_path)
                claims = register.get("claims")
                if not isinstance(claims, list) or not claims:
                    blockers.append("V2.2 claim register has no claims.")
                else:
                    pending = [str(c.get("claim_id", c.get("claim", "unknown"))) for c in claims
                               if not isinstance(c, dict) or str(c.get("status", "")).upper() != "VERIFIED"]
                    if pending:
                        blockers.append("Unverified claims remain: " + ", ".join(pending[:20]))
                reg_script_value = (register.get("script_path") or "").strip()
                reg_script = Path(reg_script_value).expanduser() if reg_script_value else None
                if reg_script is not None and not reg_script.is_absolute():
                    reg_script = ROOT / reg_script
                if script is not None and reg_script is not None and script.resolve() != reg_script.resolve():
                    blockers.append("Claim register script_path differs from the job script_path.")
            except (OSError, UnicodeError, ValueError) as exc:
                blockers.append("Could not read V2.2 claim register: {}".format(exc))

    result = {
        "schema_version": "2.5",
        "job_id": job_id,
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED" if blockers else "READY",
        "steps": steps,
        "blockers": blockers,
        "video_path": None,
        "quality_report_path": None,
        "upload_allowed": False,
        "publish_allowed": False,
        "limitations": [
            "Source discovery or a URL alone does not prove a claim true.",
            "The pipeline never simulates human fact-checking or approval.",
            "V2.4 checks file metadata, not full perceptual or factual quality.",
            "No upload, scheduling, or publishing is performed."
        ],
    }

    if blockers:
        write_new(report_path, result)
        result["report_path"] = str(report_path.resolve())
        return result

    render_script = ROOT / "src" / "render_pipeline_v2_3.py"
    step = run_step("render_local_mp4", [
        sys.executable, str(render_script), job_id, "--confirm-render", "--voice", voice
    ])
    steps.append(step)
    if step["return_code"] != 0:
        result["status"] = "RENDER_FAILED"
        result["blockers"].append("V2.3 renderer failed; see step output.")
        result["steps"] = steps
        write_new(report_path, result)
        result["report_path"] = str(report_path.resolve())
        return result

    # Find newest render manifest for this job, without changing older outputs.
    render_root = ROOT / "output" / "rendered_jobs"
    manifests = sorted(render_root.glob(job_id + "_*/render_manifest.json"),
                       key=lambda p: p.stat().st_mtime, reverse=True)
    if not manifests:
        result["status"] = "RENDER_FAILED"
        result["blockers"].append("Renderer returned success but no render manifest was found.")
    else:
        manifest_path = manifests[0]
        manifest = read_json(manifest_path)
        video_path = Path(str(manifest.get("video_path", ""))).expanduser()
        if not video_path.is_absolute():
            video_path = manifest_path.parent / video_path
        result["video_path"] = str(video_path.resolve())
        quality_script = ROOT / "src" / "final_video_quality_v2_4.py"
        quality_report = manifest_path.parent / ("final_quality_report_v2_5_" + stamp + ".json")
        step = run_step("final_mp4_metadata_gate", [
            sys.executable, str(quality_script), str(manifest_path), "--report", str(quality_report)
        ])
        steps.append(step)
        result["quality_report_path"] = str(quality_report.resolve())
        result["status"] = "RENDERED_NEEDS_HUMAN_REVIEW" if step["return_code"] == 0 else "VIDEO_QUALITY_FAILED"
        if step["return_code"] != 0:
            result["blockers"].append("Final MP4 metadata gate failed; inspect its report.")
        result["blockers"].append("Watch the complete MP4 and review factual accuracy, captions, audio, rights, and platform policy before any separate upload.")
    result["steps"] = steps
    result["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    write_new(report_path, result)
    result["report_path"] = str(report_path.resolve())
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.5 one-command local production; never uploads or publishes.")
    parser.add_argument("job_id", help="Existing pipeline job ID")
    parser.add_argument("--voice", default="en-US-AriaNeural",
                        choices=["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"])
    args = parser.parse_args(argv)
    try:
        result = run_production(args.job_id, args.voice)
        print("V2.5 STATUS: {}".format(result["status"]))
        for blocker in result.get("blockers", []):
            print("BLOCKER: " + blocker)
        if result.get("video_path"):
            print("VIDEO: {}".format(result["video_path"]))
        if result.get("quality_report_path"):
            print("QUALITY REPORT: {}".format(result["quality_report_path"]))
        print("RUN REPORT: {}".format(result.get("report_path", "")))
        print("Upload/publishing: DISABLED")
        return 0 if result["status"] == "RENDERED_NEEDS_HUMAN_REVIEW" else (2 if result["status"] == "BLOCKED" else 1)
    except (OSError, UnicodeError, ValueError, RuntimeError, KeyError, TypeError) as exc:
        print("ERROR: {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
