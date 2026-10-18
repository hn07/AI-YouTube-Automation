# V1.7 — Video Operations Dashboard

V1.7 adds a separate, read-only Streamlit dashboard. It does not replace `app.py`, alter the daily runner, render videos, or upload to YouTube.

## Features
- Summary counts for output folders, recognized report entries, upload registry items and RSS research candidates.
- Browse recent output folders, report entries, upload registry and V1.6 research candidates.
- Read recent daily/app logs.
- Refresh the displayed data manually.
- Binds to `127.0.0.1` only, not the public network.

## Update safely on Windows
```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.7-video-dashboard
TEST_V1_7.bat
```

If the local branch does not exist:
```bat
git switch -c feature/v1.7-video-dashboard --track origin/feature/v1.7-video-dashboard
```

Do not discard local changes if `git status` is not clean.

## Start
Double-click `START_DASHBOARD_V1_7.bat`, or run:
```bat
python -m streamlit run dashboard_v1_7.py --server.address 127.0.0.1 --server.port 8502
```
Then open `http://127.0.0.1:8502`. The original app can remain on port 8501.

## Data notes
The dashboard detects JSON report files inside output subfolders and reads `output/upload_registry.json` and `output/researched_topic_candidates.json`. If a previous version stores reports under another schema/path, those entries may not appear; no source files are changed. The dashboard does not write, delete or schedule any jobs.

## Test
Run `TEST_V1_7.bat`. It compiles the dashboard and exercises its read-only data loaders; it does not render or upload videos. GitHub code has not been executed on your Windows computer, so confirm the local test passes.
