# AI YouTube Automation V1.1 — Batch workflow

## What's added
- Batch Queue tab: paste one topic per line or upload a UTF-8 CSV containing a `topic` column.
- Creates up to 10 MP4 files per run, sequentially, with review-first behavior. No batch auto-upload.
- Appends outcomes to `output/batch_manifest.csv`; successful renders are marked `READY_FOR_REVIEW`, failures `FAILED`.
- Exact MP4 duplicate guard for uploads using SHA-256; successful upload records are stored in `output/upload_registry.json`.
- Uploads still require the user to review the video and check the authorization box.

## Install on Windows 11
1. Back up `D:\MyWorkSpace\AI_YouTube_Automation_V1` (copy the folder; do not overwrite credentials).
2. Open Command Prompt and run:
   ```bat
   cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1
   git status
   git fetch origin
   git checkout feature/v1.1-batch-workflow
   git pull origin feature/v1.1-batch-workflow
   ```
3. If the folder was downloaded as ZIP and has no `.git` directory, do not run those Git commands. Clone the branch into a separate folder instead:
   ```bat
   cd /d D:\MyWorkSpace
   git clone --branch feature/v1.1-batch-workflow https://github.com/hn07/AI-YouTube-Automation.git AI_YouTube_Automation_V1_1
   ```
   Copy `credentials\client_secret.json` and `credentials\token.json` from the existing local project into the new folder's `credentials` directory. Never upload or commit these files.
4. Start with `START_V1.bat` and open the local dashboard.
5. In **Batch queue**, enter two test topics and build only 2 videos first. Inspect each MP4 before uploading.

## CSV example
Save as UTF-8 `topics.csv`:

```csv
topic
Why do we dream?
How do bees communicate?
Why is the sky blue?
```

## YouTube scheduling note
V1.1 records the requested schedule and local upload ID, but that does not prove YouTube accepted a scheduled publication. Verify the video's **Visibility** in YouTube Studio. If it shows **Private** without a scheduled label/time, do not assume it will become public automatically. Open the video details and set/check the schedule manually; then test again with a future time.

## Important
- Batch rendering uses the existing template script generator, not an LLM or factual research engine. Review claims before publication.
- Batch jobs create files only; uploads are never triggered by the batch queue.
- The upload registry prevents re-uploading an identical MP4 only on this local project installation. It is not a server-side guarantee and does not detect visually similar videos with different bytes.
- Run a small test first. The GitHub branch is a development version and should be validated on your machine before replacing the stable setup.
