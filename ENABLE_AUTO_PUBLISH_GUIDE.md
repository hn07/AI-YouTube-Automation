# Automatic YouTube publishing — Windows 11

## Safety defaults
- Auto publishing is OFF in `auto-publish-config.json` (`enabled: false`).
- Do not set it to true until you have checked the video quality, Google OAuth, API quota, channel permissions, copyright/attribution and topics.
- Never commit `.env`, `client_secret.json`, `youtube_token.json`, the local SQLite database, or rendered videos.
- The runner uploads videos as **private** with a future `publishAt` time. YouTube handles public release at that scheduled time.
- Each date + slot is stored in SQLite to reduce duplicate uploads. If a network error occurs after YouTube accepted an upload but before the response returns, inspect YouTube Studio before retrying; no client can guarantee exactly-once upload in that ambiguous case.

## Daily schedule (Vietnam time, UTC+7)
| Preparation task | Target publish time | Format |
|---|---:|---|
| 04:00 | 09:00 | Shorts |
| 08:00 | 13:00 | Long-form |
| 14:00 | 19:00 | Shorts |

The preparation task must finish at least 15 minutes before its publishing time. Long-form rendering may take a long time; test actual runtime before relying on the schedule. Keep the PC awake, online, and logged in; Task Scheduler can run whether or not the UI is open, but the machine must be powered on and internet-connected.

## 1. Install
1. Checkout branch `feature/auto-publishing-v1` or download its ZIP to a new folder. Do not overwrite another working copy.
2. Install Python 3.11 or 3.12, FFmpeg and FFprobe. Confirm both `ffmpeg -version` and `ffprobe -version` work in a new Command Prompt.
3. Double-click `INSTALL_AUTO_PUBLISH.bat`.
4. Edit local `.env` in Notepad and set `OPENROUTER_API_KEY=...`. The key must stay local.
5. Ensure `client_secret.json` exists in the repository folder. Create it using Google Cloud Console: enable YouTube Data API v3; configure OAuth consent; add your account as Test user if needed; create OAuth Client ID of type Desktop app; download JSON and save as `client_secret.json`.
6. Run `TEST_AUTO_PUBLISH.bat`.

## 2. Dry-run first (no YouTube upload)
Run each slot manually in a Command Prompt from the project folder:
```bat
.venv-auto\Scripts\python.exe auto_publish.py --slot 09:00 --dry-run
.venv-auto\Scripts\python.exe auto_publish.py --slot 13:00 --dry-run
.venv-auto\Scripts\python.exe auto_publish.py --slot 19:00 --dry-run
```
Dry-run creates a script/video and checks the pipeline but does not upload. It uses real API calls and image/audio downloads and can consume free-tier limits. Verify MP4s, script, image credits and logs.

## 3. Authenticate YouTube once
Use the existing Local Studio OAuth workflow to upload a reviewed test video only after you explicitly consent, or run the first authorized auto job after enabling. The first auto job opens a Google login/consent page. Store `youtube_token.json` locally. Do not share it.

## 4. Review the config before enabling
- Edit `auto-publish-config.json`; keep `require_explicit_confirmation: true`.
- Confirm the three time slots and format mapping.
- Check `topics.txt` and adjust for the English-language US audience.
- Check the channel is eligible to schedule videos and Google API access works.
- Check video content and licensing. Automated image keyword search is imperfect; review image credits and every render during initial testing.
- To activate, change `enabled` from `false` to `true` only after all checks are passed. This is the explicit configuration switch that authorizes background uploads.

## 5. Create Windows Task Scheduler tasks
Open Task Scheduler → Create Task (not Basic Task):
- General: name `AI YouTube Auto - 09`; select `Run only when user is logged on` for the first OAuth test; do not select elevated privileges.
- Triggers: Daily, 04:00.
- Actions: Start a program. Program: full path to `.venv-auto\Scripts\python.exe`; Arguments: `auto_publish.py --slot 09:00`; Start in: full repository directory.
- Conditions: disable “Start the task only if the computer is on AC power” only if suitable; ensure the PC does not sleep during rendering.
- Settings: enable “Run task as soon as possible after a scheduled start is missed”; do not allow multiple instances.
Repeat with names/arguments:
  - `AI YouTube Auto - 13`, trigger 08:00, arguments `auto_publish.py --slot 13:00`
  - `AI YouTube Auto - 19`, trigger 14:00, arguments `auto_publish.py --slot 19:00`
- Keep the PC on and internet-connected. Test each task manually in Task Scheduler before relying on it.

## 6. Turn off quickly
Set `enabled` to `false` in `auto-publish-config.json` and disable the three tasks. This stops future jobs; it does not cancel videos already scheduled on YouTube. Cancel those in YouTube Studio if needed.

## Known limitations
- This is an initial automation runner, not a guarantee of uninterrupted operation. A long render, outage, exhausted API quota, revoked OAuth, a YouTube policy restriction, or an unavailable free model can prevent a scheduled upload.
- OpenRouter free model routing is variable and may have rate limits. For reliable 3/day publishing, a paid API may eventually be necessary.
- YouTube API projects in audit/testing status may have upload or privacy limitations. Check actual channel/project status.
- YouTube's upload endpoint can be quota-expensive. Check current Google quota before production.
- Long-form target is controlled by the renderer and AI prompt; check duration and audio/video sync before automatic publishing.
