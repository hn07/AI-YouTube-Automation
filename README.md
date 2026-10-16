# AI YouTube Automation V1 (Windows 11)

Zero-cost-first starter for producing English YouTube Shorts (30–60 seconds) from a topic, using local tools and optional free web AI.

## What V1 does
- Local dashboard (Streamlit) to enter a topic, generate a short script with a template-based fallback, create English narration with `edge-tts`, build captions, and render a vertical MP4 using FFmpeg.
- Quality checks for duration, video dimensions, output file, and missing assets.
- OAuth upload to YouTube Data API and scheduling via `status.publishAt` where the channel/API project is eligible.
- Job status, log file, and local project storage.
- No paid API key required. It does **not** bypass CAPTCHA, paywalls, rate limits, or platform protections.

## Important limitations
- The default script writer is a deterministic local template, not a free AI model. It is intentionally reliable and costs $0. You can paste a script from a free AI website into the dashboard later; web free tiers do not guarantee programmatic access.
- `edge-tts` uses Microsoft's online text-to-speech service. It has no API key/payment in normal use, but it is an online service, can change/rate-limit, and is not a fully local engine. Use only for permitted content and review current terms.
- YouTube API upload requires a Google Cloud project, YouTube Data API v3 enabled, OAuth desktop credentials, and user consent. API quotas/verification rules can apply. Videos from unverified API projects may have restrictions (e.g. private-only) until audit; verify current Google requirements.
- Scheduled publishing requires a valid future `publishAt` and eligible upload/channel state. The uploader sets the video to private with a future publish time; YouTube determines availability.
- Use only original or properly licensed media. V1 generates its own simple background graphics and does not download random Internet videos. The background music track is optional and not included.
- This is a starter project. Test with a private/unlisted upload before enabling public scheduling.

## Requirements
- Windows 10/11 x64
- Python 3.11 or 3.12 recommended (avoid untested Python 3.14 for dependency compatibility)
- Internet connection for TTS and YouTube OAuth/upload
- FFmpeg installed and available as `ffmpeg.exe` on PATH, or placed at `tools\\ffmpeg\\bin\\ffmpeg.exe`

## Quick start
1. Extract this folder to `D:\\MyWorkSpace\\AI_YouTube_Automation_V1` (or another new folder). Do not extract over an existing project.
2. Install Python 3.11/3.12 from https://www.python.org/downloads/windows/ and tick **Add Python to PATH**.
3. Install FFmpeg from https://ffmpeg.org/download.html and add its `bin` folder to PATH. Restart terminal after PATH changes.
4. Double-click `INSTALL_V1.bat`.
5. Double-click `START_V1.bat`; open the local dashboard URL shown in the terminal (normally http://127.0.0.1:8501).
6. Enter a topic, generate a script, edit/review it, then click **Create Short**.
7. Check `output\\` and `logs\\app.log`.

## YouTube OAuth setup
1. Open https://console.cloud.google.com/ and create/select a project.
2. Enable **YouTube Data API v3**.
3. Configure OAuth consent screen. If the app is in Testing, add your Google account as a test user.
4. Create OAuth Client ID -> Desktop app. Download JSON and save it as `credentials\\client_secret.json`.
5. In dashboard -> YouTube upload, set a future local publish date/time and click upload/schedule. Browser opens for consent on first run; token is saved in `credentials\\token.json`.
6. Keep both JSON files private. Never commit them to GitHub or send them to anyone.
7. If upload errors with `insufficientPermissions`, `quotaExceeded`, `videoNotFound`, `uploadLimitExceeded`, or an API verification message, follow the error details and current Google/YouTube policies. V1 never attempts to evade quota or verification.

## Cost and licensing
- Python, Streamlit, Pillow, FFmpeg: free/open-source, subject to their licenses.
- `edge-tts`: open-source client package, but the remote speech service is Microsoft's; check current service terms and suitability before commercial use.
- Generated geometric backgrounds are created by this app. No external stock footage is included.
- Any media added manually must be owned by you or licensed for the intended use.
- YouTube API is not a paid-per-upload API in normal use, but is subject to quota and policy.
- Free web AI tiers and websites may have usage limits and may not allow automation. Use them manually if automation is unsupported.

## Troubleshooting
- `ffmpeg not found`: install FFmpeg and reopen the terminal.
- TTS fails: check Internet, retry, or paste/record a permitted narration audio file (manual fallback is not yet built into this V1).
- OAuth errors: verify the JSON is a Desktop app client and API is enabled.
- Python dependency install errors: use Python 3.11/3.12; run `TEST_V1.bat` and inspect `logs\\install.log`.
- Video is rejected for quality: revise script and re-create; upload remains a separate step.

## Project layout
- `app.py`: dashboard
- `src/video_maker.py`: narration, caption timing, rendering, quality checks
- `src/youtube_uploader.py`: OAuth upload/scheduling
- `src/script_writer.py`: local no-key script generator
- `INSTALL_V1.bat`, `TEST_V1.bat`, `START_V1.bat`
