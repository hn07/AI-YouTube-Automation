# V1.8 — Offline Content Quality Gate

## Features
- Checks empty/short/long narration, repeated sentences, excessive punctuation, long all-caps words, and phrases that may need fact-checking.
- Checks title and description presence and basic length.
- Prints PASS, REVIEW, or BLOCK and can save a JSON report.
- Uses Python standard library only: no paid API, internet access, or account required.
- Does not edit source scripts, change the daily runner, render, upload, or publish.

## Safe setup on Windows 11
Use the existing folder. First inspect local changes; do not switch branches if you have uncommitted work to preserve.

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.8-content-quality
```

If the local branch does not exist:

```bat
git switch -c feature/v1.8-content-quality --track origin/feature/v1.8-content-quality
```

If `git status` shows changes, stop and preserve/review them before switching. Do not use `git reset --hard`.

## Test and use
Run `TEST_V1_8.bat`. To check a script, run `QUALITY_CHECK_V1_8.bat`, enter the full path to a UTF-8 `.txt` file, then enter the title and description. A timestamped report is saved under `output\quality_reports\`. Existing report files are never overwritten.

Command-line example:

```bat
python src\content_quality.py "C:\path\to\script.txt" --title "Creepy Facts About the Ocean" --description "Short, informative facts about the ocean." --report "output\quality_reports\ocean_quality.json"
```

Choose a new report filename if that path already exists.

## Status meanings
- **PASS**: no heuristic issues detected.
- **REVIEW**: human review recommended.
- **BLOCK**: script is empty. This is standalone and does not block the existing uploader.

## Limitations
This is not a grammar checker, plagiarism checker, or fact-checker. PASS does not guarantee truth, originality, retention, monetization eligibility, or YouTube policy compliance. Verify factual claims and manually review the finished video before publishing. V1.8 is on its own branch and does not replace V1.7.
