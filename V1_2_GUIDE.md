# AI YouTube Automation V1.2 — Reliable rendering and batch recovery

## V1.2 changes
- Rendering retries narration-duration adjustment up to two times (three render attempts total) when the voice is outside the 30–60 second target.
- Final MP4 gate checks file size, readable duration, and 1080x1920 video stream using FFmpeg/ffprobe.
- Batch processing continues after individual topic failures and records each result in `output/batch_manifest.csv`.
- Batch history includes a **Retry failed topics** action. Retry generates a new output folder; it does not upload.
- Upload UI displays status fields returned by the YouTube API. A requested publish time is not treated as proof of scheduling; verify Visibility/Schedule in YouTube Studio.
- SHA-256 duplicate upload protection remains enabled.

## Pull V1.2 into the existing Windows folder

Close the Streamlit app first. Open Command Prompt:

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git checkout feature/v1.2-reliable-render-upload
git pull origin feature/v1.2-reliable-render-upload
TEST_V1_2.bat
START_V1.bat
```

If Git reports local changes, stop and inspect them before switching branches; do not use `git reset --hard`. If the folder is a ZIP extraction without a `.git` directory, Git pull cannot work in that folder; clone the branch elsewhere or initialize a Git checkout first.

The branch is based on `feature/v1.1-batch-workflow`, so it includes V1.1 features.

## Safety and limitations
- No video is uploaded by the batch workflow.
- Auto-adjustment is limited to two retries; unusual narration may still need manual editing.
- Caption burning can fall back to an uncaptioned MP4 if FFmpeg's subtitle filter fails; the file must still pass the MP4 quality gate.
- YouTube API response fields are shown when returned, but Studio remains the final confirmation of a scheduled publish. OAuth/API eligibility and YouTube policies can affect scheduling.
- Script generation remains template-based, not a factual research or fact-checking engine. Review all claims and rights before upload.
- Keep `credentials\client_secret.json` and `credentials\token.json` local and private. They must never be committed.
- Output, logs, work files, and local upload registry are local data and should be preserved when updating code.
