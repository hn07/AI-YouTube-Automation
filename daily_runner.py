"""Daily unattended runner for V1.3.

Run once per day from Windows Task Scheduler. Renders a batch first, then uploads
and asks YouTube to schedule each video in a distinct future Vietnam-time slot.
"""
import json
import logging
import re
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

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


def main():
    started = datetime.now(TZ)
    run_id = started.strftime("%Y%m%d_%H%M%S")
    log.info("=== Daily V1.3 run started id=%s ===", run_id)
    if not (ROOT / "credentials" / "client_secret.json").exists():
        raise FileNotFoundError("Missing credentials/client_secret.json")
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
            rendered.append({"topic": topic, "script": script, "path": mp4, "duration": duration, "status": "RENDERED"})
            log.info("Render OK topic=%s path=%s duration=%.2f", topic, mp4, duration)
        except Exception as exc:
            log.exception("Render failed topic=%s", topic)
            rendered.append({"topic": topic, "script": "", "path": None, "duration": 0, "status": "RENDER_FAILED", "error": str(exc)})

    # Assign future slots only after rendering, so slow rendering cannot make the requested time stale.
    ready = [item for item in rendered if item["status"] == "RENDERED"]
    slots = next_distinct_slots(len(ready))
    report = []
    for idx, (item, publish_at) in enumerate(zip(ready, slots), 1):
        path = item["path"]
        title = item["topic"][:100]
        if find_duplicate(path):
            log.warning("Duplicate MP4 blocked: %s", path)
            report.append({"topic": item["topic"], "status": "DUPLICATE_BLOCKED", "path": str(path), "publish_at": publish_at.isoformat()})
            continue
        try:
            description = (
                "A quick, clear explainer. Please check reliable sources for more detail.\n\n"
                "#Shorts #Facts #LearnSomething"
            )
            response = upload_and_schedule(
                str(path), title, description,
                ["shorts", "facts", "learning", "explainer"],
                publish_at, privacy="private",
            )
            video_id = str(response.get("id", ""))
            if not video_id:
                raise RuntimeError("YouTube upload returned no video ID; inspect logs before retrying.")
            # Record immediately after upload so a verification issue never triggers a duplicate upload.
            record_upload(str(path), video_id, title, publish_at.isoformat())
            verified = bool(response.get("schedule_verified"))
            status = "SCHEDULED_VERIFIED" if verified else "UPLOADED_SCHEDULE_UNVERIFIED"
            report.append({
                "topic": item["topic"], "status": status, "video_id": video_id,
                "path": str(path), "publish_at": publish_at.isoformat(),
                "verification_error": response.get("verification_error", ""),
            })
            log.info("Upload complete topic=%s video_id=%s status=%s publish_at=%s", item["topic"], video_id, status, publish_at.isoformat())
        except Exception as exc:
            log.exception("Upload/schedule failed topic=%s", item["topic"])
            report.append({"topic": item["topic"], "status": "UPLOAD_FAILED", "path": str(path),
                           "publish_at": publish_at.isoformat(), "error": str(exc)})

    for item in rendered:
        if item["status"] != "RENDERED":
            report.append({"topic": item["topic"], "status": item["status"], "error": item.get("error", "")})
    report_path = ROOT / "output" / f"daily_report_{run_id}.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    good = sum(1 for x in report if x.get("status") == "SCHEDULED_VERIFIED")
    uncertain = sum(1 for x in report if x.get("status") == "UPLOADED_SCHEDULE_UNVERIFIED")
    failed = sum(1 for x in report if x.get("status") in {"UPLOAD_FAILED", "RENDER_FAILED", "DUPLICATE_BLOCKED"})
    log.info("Run complete: verified=%d unverified=%d failed=%d report=%s", good, uncertain, failed, report_path)
    print(json.dumps({"report": str(report_path), "verified": good, "unverified": uncertain, "failed": failed}, ensure_ascii=False, indent=2))
    return 0 if failed == 0 and uncertain == 0 else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        logging.exception("Fatal daily runner error")
        print(f"FATAL: {exc}")
        traceback.print_exc()
        sys.exit(1)
