import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from src.script_writer import generate_script, estimate_seconds, clean_topic
from src.video_maker import render_short

ROOT = Path(__file__).resolve().parent
for folder in ["logs", "output", "work", "credentials"]:
    (ROOT/folder).mkdir(exist_ok=True)
logging.basicConfig(
    filename=ROOT/"logs"/"app.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    encoding="utf-8",
)
log = logging.getLogger("ytauto")
st.set_page_config(page_title="AI YouTube Automation V1", page_icon="🎬", layout="wide")
st.title("🎬 AI YouTube Automation V1")
st.caption("Windows 11 • Zero-cost-first • English YouTube Shorts • Local dashboard")

with st.sidebar:
    st.header("Settings")
    voice = st.selectbox("English narration voice", ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"], index=0)
    style = st.selectbox("Script style", ["curiosity", "story"])
    tz_name = st.selectbox("Schedule timezone", ["Asia/Ho_Chi_Minh", "America/Los_Angeles", "America/New_York", "UTC"], index=0)
    st.info("V1 generates an original graphic background. No stock footage or music is bundled.")

tab_create, tab_upload, tab_help = st.tabs(["1. Create Short", "2. Upload / Schedule", "3. Setup & status"])
with tab_create:
    st.subheader("Create a Short")
    topic = st.text_input("Video topic (change this any time)", "Why do we dream?")
    st.caption("Tip: choose a narrow topic that can be explained in one clear idea.")
    if "script" not in st.session_state:
        st.session_state.script = generate_script(topic, style)
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Generate starter script", use_container_width=True):
            st.session_state.script = generate_script(topic, style)
            st.success("Draft generated locally. This is a template-based starter; verify factual claims and edit before rendering.")
    with c2:
        words = len(re.findall(r"\b[\w'-]+\b", st.session_state.script))
        est = estimate_seconds(st.session_state.script)
        st.metric("Word count", words)
        st.metric("Estimated narration", f"{est} sec")
    script = st.text_area("Review/edit English narration (recommended 75–130 words)", value=st.session_state.script, height=260, key="script_edit")
    st.session_state.script = script
    st.caption("To use a free web AI: create your script there, then paste it here. Do not automate a website if its terms do not permit it.")
    if st.button("🎞️ Create Short (MP4)", type="primary", use_container_width=True):
        if not topic.strip() or len(script.split()) < 60:
            st.error("Add a topic and at least 60 words. Aim for 75–130 words.")
        else:
            slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", topic).strip("_")[:45] or "short"
            job_dir = ROOT/"output"/(datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+slug)
            try:
                with st.spinner("Generating narration and rendering 1080×1920 video..."):
                    mp4, duration = render_short(topic, script, job_dir, voice)
                st.session_state.latest_video = str(mp4)
                st.session_state.latest_topic = topic
                st.session_state.latest_script = script
                st.session_state.latest_dir = str(job_dir)
                log.info("Created %s duration=%.2f", mp4, duration)
                st.success(f"Created and passed basic quality checks: {duration:.1f} seconds")
                st.video(str(mp4))
                st.download_button("Download MP4", data=mp4.read_bytes(), file_name="youtube_short.mp4", mime="video/mp4")
            except Exception as e:
                log.exception("Create Short failed")
                st.error(f"Creation failed: {e}")
                st.caption("Check logs/app.log. No upload was attempted.")

with tab_upload:
    st.subheader("Upload and schedule")
    st.warning("YouTube upload is a real external action. Start with a private test upload. Scheduling and public publishing depend on channel/API eligibility.")
    latest = st.session_state.get("latest_video", "")
    video_path = st.text_input("Video MP4 path", latest)
    default_title = st.session_state.get("latest_topic", "A quick fact worth knowing")
    title = st.text_input("YouTube title (English)", default_title[:95])
    desc_default = "A quick, clear explainer. Subscribe for more Shorts.\n\n#Shorts #Facts #LearnSomething"
    description = st.text_area("Description", desc_default, height=100)
    tags_text = st.text_input("Tags (comma-separated)", "shorts, facts, learning, explainer")
    privacy = st.selectbox("Upload privacy", ["private", "unlisted", "public"], index=0)
    schedule_date = st.date_input("Publish date", value=(datetime.now(ZoneInfo(tz_name))+timedelta(days=1)).date())
    schedule_time = st.time_input("Publish time", value=datetime.now(ZoneInfo(tz_name)).replace(hour=18, minute=0, second=0, microsecond=0).time())
    confirm = st.checkbox("I reviewed this video, have rights to all media, and authorize upload to my YouTube channel.")
    if st.button("Upload / Schedule on YouTube", type="primary", use_container_width=True):
        try:
            if not video_path or not Path(video_path).exists():
                raise FileNotFoundError("Select an existing MP4 file.")
            if not confirm:
                raise ValueError("Confirm review and rights before uploading.")
            if privacy == "public":
                st.info("A future publish time with public privacy is not always accepted by the API. The uploader uses private + future publishAt for scheduled publishing.")
            from src.youtube_uploader import upload_and_schedule
            local_dt = datetime.combine(schedule_date, schedule_time).replace(tzinfo=ZoneInfo(tz_name))
            if local_dt <= datetime.now(ZoneInfo(tz_name)):
                raise ValueError("Choose a future publish date/time.")
            with st.spinner("Opening Google OAuth if needed, then uploading..."):
                response = upload_and_schedule(
                    video_path, title, description,
                    [x.strip() for x in tags_text.split(",") if x.strip()],
                    local_dt, privacy="private"
                )
            st.success("Upload accepted by YouTube. Verify the status in YouTube Studio.")
            st.write({"video_id": response.get("id"), "scheduled_time": local_dt.isoformat(),
                      "privacy_requested": "private with scheduled publish time"})
            st.link_button("Open YouTube Studio", "https://studio.youtube.com/")
            log.info("Uploaded video id=%s", response.get("id"))
        except Exception as e:
            log.exception("Upload/schedule failed")
            st.error(f"Upload/schedule failed: {e}")
            st.caption("No quota or access restrictions are bypassed. Check OAuth setup and logs/app.log.")

with tab_help:
    st.subheader("Setup checklist")
    checks = {
        "Python virtual environment": (ROOT/"venv"/"Scripts"/"python.exe").exists(),
        "FFmpeg available": __import__("shutil").which("ffmpeg") is not None or (ROOT/"tools"/"ffmpeg"/"bin"/"ffmpeg.exe").exists(),
        "YouTube OAuth client JSON": (ROOT/"credentials"/"client_secret.json").exists(),
        "YouTube token already authorized": (ROOT/"credentials"/"token.json").exists(),
    }
    for name, ok in checks.items():
        st.write(("✅ " if ok else "⬜ ") + name)
    st.markdown("""
**Important:** this V1 uses a template script generator, not an LLM. You may paste a script from a free AI website into the editor.
- Install full FFmpeg build including `ffmpeg.exe` and `ffprobe.exe`.
- Keep OAuth client and token JSON private.
- Generated background art is original and locally rendered.
- Voice is generated by the `edge-tts` client using an online Microsoft speech endpoint; service access and terms can change.
- Review every script and use factual sources. This starter does not automatically fact-check claims or search the web.
- Logs: `logs/app.log`; installer log: `logs/install.log`; tests: `logs/test.log`.
""")
