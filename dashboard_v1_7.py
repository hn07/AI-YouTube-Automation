"""Standalone read-only operations dashboard for AI YouTube Automation V1.7."""
import json
from datetime import datetime
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
LOGS = ROOT / "logs"


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return default


def load_jobs():
    jobs = []
    if not OUTPUT.exists():
        return jobs
    for folder in sorted((p for p in OUTPUT.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime, reverse=True):
        report_files = list(folder.glob("*report*.json")) + list(folder.glob("report.json"))
        for report_file in report_files:
            data = read_json(report_file, None)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        jobs.append({"job": folder.name, "report": report_file.name, **item})
            elif isinstance(data, dict):
                entries = data.get("items") or data.get("results") or data.get("videos") or []
                if isinstance(entries, list):
                    for item in entries:
                        if isinstance(item, dict):
                            jobs.append({"job": folder.name, "report": report_file.name, **item})
    return jobs


def load_registry():
    value = read_json(OUTPUT / "upload_registry.json", [])
    return value if isinstance(value, list) else []


def load_research():
    value = read_json(OUTPUT / "researched_topic_candidates.json", {})
    items = value.get("items", []) if isinstance(value, dict) else []
    return items if isinstance(items, list) else []


st.set_page_config(page_title="AI YouTube Automation V1.7", page_icon="🎬", layout="wide")
st.title("🎬 AI YouTube Automation — V1.7")
st.caption("Local operations dashboard · Read-only · Does not render, upload, or modify queue files")
if st.button("↻ Refresh data"):
    st.rerun()

jobs = load_jobs()
registry = load_registry()
research = load_research()
video_dirs = [p for p in OUTPUT.iterdir() if p.is_dir()] if OUTPUT.exists() else []
failed = sum(1 for x in jobs if "FAIL" in str(x.get("status", "")).upper() or "ERROR" in str(x.get("status", "")).upper())
c1, c2, c3, c4 = st.columns(4)
c1.metric("Output jobs", len(video_dirs))
c2.metric("Report entries", len(jobs))
c3.metric("Registry uploads", len(registry))
c4.metric("Research candidates", len(research))

tab_jobs, tab_uploads, tab_research, tab_logs = st.tabs(["Video jobs", "Upload registry", "Research queue", "Recent logs"])
with tab_jobs:
    st.subheader("Local job/report overview")
    if jobs:
        st.dataframe(jobs, use_container_width=True, hide_index=True)
    else:
        st.info("No recognized report entries yet. This dashboard currently detects JSON reports inside output subfolders.")
    if video_dirs:
        st.caption("Recent output folders")
        st.dataframe([{"folder": p.name, "modified": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"), "path": str(p)} for p in sorted(video_dirs, key=lambda p: p.stat().st_mtime, reverse=True)[:50]], use_container_width=True, hide_index=True)
with tab_uploads:
    st.subheader("Recorded YouTube uploads")
    if registry:
        st.dataframe(registry, use_container_width=True, hide_index=True)
    else:
        st.info("Upload registry is empty or not created yet.")
with tab_research:
    st.subheader("RSS topic candidates")
    if research:
        st.dataframe([{"topic": x.get("topic", ""), "published": x.get("published", ""), "source_url": x.get("source_url", ""), "summary": x.get("summary", "")} for x in research], use_container_width=True, hide_index=True)
        st.warning("These are discovery leads, not fact-checked claims. Open source links and verify before scripting.")
    else:
        st.info("No research queue found. Run RESEARCH_TOPICS_V1_6.bat to create one.")
with tab_logs:
    st.subheader("Recent log lines")
    log_path = LOGS / "daily_automation.log"
    if not log_path.exists():
        log_path = LOGS / "app.log"
    if log_path.exists():
        try:
            lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
            st.code("\n".join(lines[-150:]) or "Log file is empty")
        except OSError as exc:
            st.error(f"Could not read log: {exc}")
    else:
        st.info("No application log file found yet.")

st.divider()
st.caption("V1.7 is a read-only dashboard. It does not trigger uploads or change YouTube videos.")
