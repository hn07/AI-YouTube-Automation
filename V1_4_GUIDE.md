# V1.4 — Reliable Automation & Recovery

V1.4 builds on the V1.3 daily scheduler in a separate branch. It does not overwrite the V1.3 branch.

## Changes
- Adds an OS-level single-instance lock so two scheduled/manual runs cannot upload at the same time. The OS releases the lock if Python exits/crashes.
- Runs a preflight check for OAuth client, FFmpeg, and FFprobe before doing expensive work.
- Checks that each rendered MP4 exists, is not suspiciously small, and has a positive duration before upload.
- Writes the JSON run report atomically.
- Fails closed if the upload registry cannot be read.
- Uses a review-required status after ambiguous upload errors; do not blindly retry, because YouTube may have accepted the upload even if the connection failed.
- Keeps topic selection from the local bank; this version does not add LLM research or fact-checking.

## Safe update in the existing folder
Close Streamlit first. Back up any uncommitted changes or check `git status` before switching branches.

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.4-reliable-automation
```

If the branch does not exist locally:
```bat
git switch -c feature/v1.4-reliable-automation --track origin/feature/v1.4-reliable-automation
```

Run the static check:
```bat
TEST_V1_4.bat
```

The test does not upload videos. Review `logs\v1_4_test.log`. This branch has not yet been executed on the user's Windows PC, so the local test is required.

## Important
- Do not run `RUN_DAILY_AUTOMATION.bat` until ready for real uploads; it performs real uploads.
- Keep OAuth JSON/token files private and out of Git.
- Before retrying any `UPLOAD_FAILED_REVIEW_BEFORE_RETRY` job, inspect YouTube Studio and `output\upload_registry.json` first.
- Schedule the Windows task only after manual execution and YouTube Studio checks succeed.
