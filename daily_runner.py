"""Reliable daily runner for V1.4.

Renders valid MP4 files, prevents overlapping runs, writes an atomic JSON report,
and never blindly retries an upload after an ambiguous result.
"""
import json
import logging
import re
import shutil
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.run_guard import single_instance_lock
from src.script_writer import generate_script
from src.topic_generator import generate_daily_topics
from src.video_maker import render_short
from src.upload_registry import find_duplicate, record_upload
from src.youtube_uploader import upload_and_schedule

ROOT = Path(__file__).resolve().parent
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SLOTS = [(7, 0), (11, 0), (18, 0)]
LOG_PATH = ROOT / "logs" / "daily_automation.log"
(ROOT / "logs").mkdir(exist_ok=True)
(ROOT / "output").mkdir(exist_ok=True)
logging.basicConfig(filename=LOG_PATH, level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s", encoding="utf-8")
log = logging.getLogger("ytauto.daily")


def next_distinct_slots(count, now=None):
    now = (now or datetime.now(TZ)).astimezone(TZ)
    result = []
    day = now.date()
    while len(result) < count:
        for hour, minute in SLOTS:
            candidate = datetime.combine(day, datetime.min.time(), tzinfo=TZ).replace(hour=hour, minute=minute)
            if candidate > now and candidate not in result:
                result.append(candidate)
                if len(result) >= count:
                    break
        day += timedelta(days=1)
    return result


def write_report(report_path, report):
    """Write report atomically so a power loss cannot leave half-written JSON."""
    temp_path = report_path.with_suffix(report_path.suffix + ".tmp")
    temp_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temp_path.replace(report_path)


def check_preflight():
    if not (ROOT / "credentials" / "client_secret.json").exists():
        raise FileNotFoundError("Missing credentials/client_secret.json")
    if not shutil.which("ffmpeg") and not (ROOT / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe").exists():
        raise FileNotFoundError("FFmpeg not found on PATH or tools/ffmpeg/bin/ffmpeg.exe")
    if not shutil.which("ffprobe") and not (ROOT / "tools" / "ffmpeg" / "bin" / "ffprobe.exe").exists():
        # A custom FFmpeg location may still be used by the renderer, so fail early with a clear message.
        raise FileNotFoundError("FFprobe not found on PATH or tools/ffmpeg/bin/ffprobe.exe")


def run_daily():
    started = datetime.now(TZ)
    run_id = started.strftime("%Y%m%d_%H%M%S")
    log.info("=== Daily V1.4 run started id=%s ===", run_id)
    check_preflight()
    topics = generate_daily_topics(3)
    log.info("Generated topics: %s", topics)
    rendered = []
    for idx, topic in enumerate(topics, 1):
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", topic).strip("_")[:45] or "short"
        job_dir = ROOT / "output" / f"{run_id}_daily{idx}_{slug}"
        try:
            script = generate_script(topic, "curiosity")
            log.info("Rendering %d/3 topic=%s", idx, topic)
            mp4, duration = render_short(topic, script, job_dir, "en-US-AriaNeural")
            path = Path(mp4)
            if not path.is_file():
                raise RuntimeError(f"Renderer returned a missing video file: {path}")
            if path.stat().st_size < 10_000:
                raise RuntimeError(f"Rendered MP4 is suspiciously small ({path.stat().st_size} bytes): {path}")
            if float(duration) <= 0:
                raise RuntimeError(f"Renderer returned invalid duration: {duration}")
            rendered.append({"topic": topic, "script": script, "path": str(path), "duration": float(duration), "status": "RENDERED"})
            log.info("Render OK topic=%s path=%s duration=%.2f size=%d", topic, path, duration, path.stat().st_size)
        except Exception as exc:
            log.exception("Render failed topic=%s", topic)
            rendered.append({"topic": topic, "script": "", "path": None, "duration": 0, "status": "RENDER_FAILED", "error": str(exc)})

    ready = [item for item in rendered if item["status"] == "RENDERED"]
    slots = next_distinct_slots(len(ready))
    report = []
    for item, publish_at in zip(ready, slots):
        path = item["path"]
        title = item["topic"][:100]
        try:
            duplicate = find_duplicate(path)
            if duplicate:
                log.warning("Duplicate MP4 blocked: %s (video_id=%s)", path, duplicate.get("video_id", "unknown"))
                report.append({"topic": item["topic"], "status": "DUPLICATE_BLOCKED", "path": path,
                               "existing_video_id": duplicate.get("video_id"), "publish_at": publish_at.isoformat()})
                continue
        except Exception as exc:
            # A corrupt/unreadable registry must stop uploads; fail closed to avoid duplicates.
            log.exception("Cannot safely check upload registry; refusing upload")
            report.append({"topic": item["topic"], "status": "REGISTRY_CHECK_FAILED", "path": path,
                           "publish_at": publish_at.isoformat(), "error": str(exc)})
            continue

        try:
            description = (
                "A quick, clear explainer. Please check reliable sources for more detail.\n\n"
                "#Shorts #Facts #LearnSomething"
            )
            response = upload_and_schedule(
                path, title, description, ["shorts", "facts", "learning", "explainer"],
                publish_at, privacy="private",
            )
            video_id = str(response.get("id", ""))
            if not video_id:
                raise RuntimeError(
                    "Upload result is ambiguous: YouTube returned no video ID. "
                    "Inspect YouTube Studio before manually retrying."
                )
            # Register as soon as an ID is returned, even when schedule verification fails.
            record_upload(path, video_id, title, publish_at.isoformat())
            verified = bool(response.get("schedule_verified"))
            status = "SCHEDULED_VERIFIED" if verified else "UPLOADED_SCHEDULE_UNVERIFIED"
            report.append({
                "topic": item["topic"], "status": status, "video_id": video_id, "path": path,
                "publish_at": publish_at.isoformat(),
                "verification_error": response.get("verification_error", ""),
            })
            log.info("Upload result topic=%s video_id=%s status=%s publish_at=%s",
                     item["topic"], video_id, status, publish_at.isoformat())
        except Exception as exc:
            # Upload exceptions can be ambiguous if the connection dropped after YouTube accepted the file.
            log.exception("Upload/schedule failed topic=%s; manual review required before retry", item["topic"])
            report.append({"topic": item["topic"], "status": "UPLOAD_FAILED_REVIEW_BEFORE_RETRY",
                           "path": path, "publish_at": publish_at.isoformat(), "error": str(exc)})

    for item in rendered:
        if item["status"] != "RENDERED":
            report.append({"topic": item["topic"], "status": item["status"], "error": item.get("error", "")})

    report_path = ROOT / "output" / f"daily_report_{run_id}.json"
    write_report(report_path, report)
    good = sum(1 for x in report if x.get("status") == "SCHEDULED_VERIFIED")
    uncertain = sum(1 for x in report if x.get("status") == "UPLOADED_SCHEDULE_UNVERIFIED")
    failed = sum(1 for x in report if x.get("status") not in {"SCHEDULED_VERIFIED", "UPLOADED_SCHEDULE_UNVERIFIED"})
    summary = {"run_id": run_id, "report": str(report_path), "verified": good,
               "unverified": uncertain, "failed_or_review": failed}
    log.info("Run complete: %s", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if failed == 0 and uncertain == 0 else 2


def main():
    lock_path = ROOT / "output" / ".daily_runner.lock"
    with single_instance_lock(lock_path):
        return run_daily()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        logging.exception("Fatal daily runner error")
        print(f"FATAL: {exc}")
        traceback.print_exc()
        sys.exit(1)
