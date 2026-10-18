from __future__ import annotations
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, date, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "auto-publish-config.json"
TOPICS_PATH = ROOT / "topics.txt"
ENV_PATH = ROOT / ".env"
STATE_DB = ROOT / "auto-publish-state.sqlite3"
OUTPUT_ROOT = ROOT / "local-output"
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def load_env_file():
    if not ENV_PATH.exists():
        return
    for raw in ENV_PATH.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

def read_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

def log(message):
    stamp = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    line = f"[{stamp}] {message}"
    print(line, flush=True)
    (ROOT / "auto-publish.log").open("a", encoding="utf-8").write(line + "\n")

def init_db():
    with sqlite3.connect(STATE_DB) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS jobs (
            publish_date TEXT NOT NULL, slot TEXT NOT NULL, topic TEXT NOT NULL,
            status TEXT NOT NULL, video_id TEXT, details TEXT, updated_at TEXT NOT NULL,
            PRIMARY KEY (publish_date, slot))""")

def already_done(day, slot):
    with sqlite3.connect(STATE_DB) as db:
        row = db.execute("SELECT status, video_id FROM jobs WHERE publish_date=? AND slot=?",
                         (day.isoformat(), slot)).fetchone()
    return row if row and row[0] in ("uploaded", "processing") else None

def record(day, slot, topic, status, video_id=None, details=""):
    with sqlite3.connect(STATE_DB) as db:
        db.execute("""INSERT INTO jobs(publish_date,slot,topic,status,video_id,details,updated_at)
            VALUES(?,?,?,?,?,?,?) ON CONFLICT(publish_date,slot) DO UPDATE SET
            topic=excluded.topic,status=excluded.status,video_id=excluded.video_id,
            details=excluded.details,updated_at=excluded.updated_at""",
            (day.isoformat(), slot, topic, status, video_id, details,
             datetime.now(LOCAL_TZ).isoformat()))

def choose_topic(day, slot):
    topics = [x.strip() for x in TOPICS_PATH.read_text(encoding="utf-8-sig").splitlines()
              if x.strip() and not x.strip().startswith("#")]
    if not topics:
        raise RuntimeError("topics.txt chưa có chủ đề.")
    # Stable selection for a given date/slot; no extra state needed.
    index = (day.toordinal() * 3 + int(slot[:2]) // 4) % len(topics)
    return topics[index]

def generate_script(topic, long_form, model):
    import requests
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key or key == "replace_with_your_key":
        raise RuntimeError("Thiếu OPENROUTER_API_KEY trong tệp .env cục bộ.")
    target = "900–1300" if long_form else "120–160"
    prompt = (
        "Write an original English YouTube narration for a US audience. "
        f"Topic: {topic}. Target {target} words. "
        "Use a compelling hook, concrete but verifiable explanations, clear transitions, "
        "and a memorable ending. Do not invent statistics, quotes, sources, or facts. "
        "Avoid repetitive filler. Return narration only."
    )
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
                 "HTTP-Referer": "http://localhost", "X-Title": "AI-YouTube-Automation"},
        json={"model": model, "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.7, "max_tokens": 2200}, timeout=120)
    if not response.ok:
        raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {response.text[:800]}")
    script = response.json()["choices"][0]["message"]["content"].strip()
    minimum = 450 if long_form else 70
    if len(script.split()) < minimum:
        raise RuntimeError(f"Kịch bản AI quá ngắn ({len(script.split())} từ); không tự đăng.")
    return script

def upload_scheduled(video_path, title, description, publish_dt, config):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload

    client_file = ROOT / "client_secret.json"
    token_file = ROOT / "youtube_token.json"
    if not client_file.exists():
        raise RuntimeError("Thiếu client_secret.json; hoàn tất Google OAuth trước.")
    creds = Credentials.from_authorized_user_file(str(token_file), SCOPES) if token_file.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(client_file), SCOPES)
            creds = flow.run_local_server(port=0, prompt="consent")
        token_file.write_text(creds.to_json(), encoding="utf-8")
    youtube = build("youtube", "v3", credentials=creds)
    body = {"snippet": {"title": title[:100], "description": description[:5000],
                        "categoryId": str(config.get("category_id", "22"))},
            "status": {"privacyStatus": "private",
                       "publishAt": publish_dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                       "selfDeclaredMadeForKids": bool(config.get("made_for_kids", False))}}
    request = youtube.videos().insert(part="snippet,status",
        body=body, media_body=MediaFileUpload(str(video_path), mimetype="video/*", resumable=True))
    response = request.execute()
    return response.get("id", "")

def run_slot(slot, force_dry_run=False):
    load_env_file()
    config = read_config()
    init_db()
    if not force_dry_run:
        if config.get("enabled") is not True:
            raise RuntimeError("Tự động đăng đang TẮT. Chỉ đổi enabled=true sau khi OAuth, API key, kênh và quyền sử dụng nội dung đã được kiểm tra.")
        if config.get("require_explicit_confirmation") is not True:
            raise RuntimeError("Thiếu cờ require_explicit_confirmation=true; dừng an toàn.")
    slots = {x["publish_time"]: x for x in config.get("slots", [])}
    if slot not in slots:
        raise RuntimeError(f"Không có khung giờ {slot} trong auto-publish-config.json.")
    item = slots[slot]
    now = datetime.now(LOCAL_TZ)
    target_day = now.date()
    publish_dt = datetime.combine(target_day, datetime.strptime(slot, "%H:%M").time(), tzinfo=LOCAL_TZ)
    if publish_dt <= now + timedelta(minutes=15):
        raise RuntimeError(f"Đã quá sát giờ đăng {slot}; bỏ qua để tránh đặt lịch sai. Chạy tác vụ chuẩn bị sớm hơn.")
    previous = already_done(target_day, slot)
    if previous:
        log(f"Bỏ qua {target_day} {slot}: trạng thái đã là {previous[0]}, video_id={previous[1]}.")
        return
    topic = choose_topic(target_day, slot)
    long_form = item["format"] == "long"
    log(f"Bắt đầu slot={slot}, format={item['format']}, topic={topic!r}.")
    record(target_day, slot, topic, "processing", details="Rendering started")
    job_name = datetime.now(LOCAL_TZ).strftime("%Y%m%d_%H%M%S") + "_" + re.sub(r"[^A-Za-z0-9_-]+", "_", topic)[:36]
    job = OUTPUT_ROOT / job_name
    job.mkdir(parents=True, exist_ok=False)
    try:
        script = generate_script(topic, long_form, config.get("openrouter_model", "openrouter/free"))
        (job / "script.txt").write_text(script + "\n", encoding="utf-8")
        (job / "topic.txt").write_text(topic + "\n", encoding="utf-8")
        renderer = ROOT / "src" / ("web_long_renderer.py" if long_form else "web_short_renderer.py")
        env = os.environ.copy()
        env.update({"TOPIC": topic, "SCRIPT_TEXT": script,
                    "VOICE": config.get("voice", "en-US-AriaNeural"), "PYTHONIOENCODING": "utf-8"})
        ffmpeg = shutil_which("ffmpeg")
        ffprobe = shutil_which("ffprobe")
        if not ffmpeg or not ffprobe:
            raise RuntimeError("Không tìm thấy ffmpeg và ffprobe trong PATH.")
        timeout = int(config.get("max_render_minutes", 90)) * 60
        result = subprocess.run([sys.executable, str(renderer)], cwd=str(job), env=env,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        (job / "render.log").write_text((result.stdout or "") + "\n--- STDERR ---\n" + (result.stderr or ""), encoding="utf-8")
        if result.returncode:
            raise RuntimeError("Dựng video lỗi; xem local-output/" + job.name + "/render.log")
        render_dir = job / ("rendered-long-draft" if long_form else "rendered-draft")
        video = render_dir / ("youtube_long_draft.mp4" if long_form else "youtube_short_draft.mp4")
        if not video.exists() or video.stat().st_size < 100_000:
            raise RuntimeError("Không tìm thấy MP4 hợp lệ sau khi dựng.")
        if force_dry_run:
            log(f"DRY RUN OK: {video}; không upload.")
            record(target_day, slot, topic, "dry_run_ok", details=str(video))
            return
        description = (f"{topic}\n\nSubscribe for more curious stories and explainers.\n\n"
                       "Visual sources and license details are included in the local video package. "
                       "Please review the rendered video and source credits before enabling automatic publication.")
        video_id = upload_scheduled(video, topic, description, publish_dt, config)
        record(target_day, slot, topic, "uploaded", video_id=video_id,
               details=f"Scheduled for {publish_dt.isoformat()}; file={video}")
        log(f"UPLOAD OK: video_id={video_id}; scheduled={publish_dt.isoformat()}")
    except Exception as exc:
        record(target_day, slot, topic, "failed", details=str(exc))
        log(f"FAILED slot={slot}: {exc}")
        raise

def shutil_which(name):
    import shutil
    return shutil.which(name)

def main():
    parser = argparse.ArgumentParser(description="Generate and schedule one YouTube video for a configured daily slot.")
    parser.add_argument("--slot", required=True, choices=["09:00", "13:00", "19:00"])
    parser.add_argument("--dry-run", action="store_true", help="Generate video but do not upload; does not require enabled=true.")
    args = parser.parse_args()
    try:
        run_slot(args.slot, force_dry_run=args.dry_run)
    except Exception as exc:
        log(f"STOPPED: {exc}")
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
