# V1.3 — Daily topic generation and scheduled Shorts

## Your selected schedule
- Generate 3 English Shorts topics every day.
- Request YouTube publish times at **07:00, 11:00, and 18:00 Asia/Ho_Chi_Minh (Vietnam time)**.
- Topics are selected from a curated local topic bank without a paid API key. Recent exact topics are stored in `output/topic_history.json` and avoided until the bank cycles.
- The runner renders all 3 videos first, then assigns distinct future slots. If rendering runs past a slot, it chooses the next future slot rather than submitting a past time.
- A daily Windows task can run at 01:00 and writes logs to `logs/daily_automation.log` and a JSON report to `output/daily_report_*.json`.

## Update in the existing folder

Close Streamlit first. From Command Prompt:

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.3-daily-auto-scheduler
```

If the local branch does not exist:
```bat
git switch -c feature/v1.3-daily-auto-scheduler --track origin/feature/v1.3-daily-auto-scheduler
```

Run the existing syntax/dependency check:
```bat
TEST_V1_2.bat
```

Then run `RUN_DAILY_AUTOMATION.bat` manually. It will generate/render/upload three videos and therefore performs real uploads. Run it only when you are ready and the correct YouTube channel is authorized. If OAuth opens a browser, finish consent and rerun if the first attempt did not complete all jobs.

Only after the manual run and YouTube Studio checks, install the daily task:
```bat
INSTALL_DAILY_TASK.bat
```

## Important
- This is an unattended upload workflow. It uploads videos to the connected channel; there is no per-video approval in the scheduled run.
- Keep `credentials\client_secret.json` and `credentials\token.json` private. Never commit them.
- The PC must be powered on, connected to the Internet, and awake at 01:00. Task Scheduler runs as your Windows user.
- The local topic generator does not use an LLM, browse sources, or fact-check claims. It avoids recent exact topic repeats but cannot guarantee global novelty or factual accuracy.
- Scheduling is considered confirmed only when a follow-up YouTube API status query returns the expected future `publishAt` and `privacyStatus=private`. If upload is accepted but verification fails, the runner records the video ID and flags it for manual review; it does not blindly upload the same MP4 again.
- YouTube API quotas, channel eligibility, OAuth scopes, Google verification, upload restrictions, and policies can block uploads/scheduling. This code does not bypass them.
- Do not run two copies of the daily runner simultaneously.
