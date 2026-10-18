# V1.9 — Shorts Retention Structure Review

## What it does
- Reviews opening hook cues, generic introductions, sentence length, filler phrases, ending/payoff cues, and rough narration length.
- Produces PASS / REVIEW / BLOCK plus actionable suggestions.
- Saves timestamped JSON reports when run via the included BAT file.
- Uses Python standard library only; no paid AI API or internet is required.
- Does not modify V1.8, the daily runner, source scripts, video files, or YouTube uploads.

## Safe setup
In the existing project folder, inspect local changes first. Do not switch branches with uncommitted work you need to preserve.

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.9-shorts-retention-check
```

If the local branch does not exist:
```bat
git switch -c feature/v1.9-shorts-retention-check --track origin/feature/v1.9-shorts-retention-check
```

If `git status` shows changes, stop and preserve/review them before switching. Do not use `git reset --hard`.

## Test and run
1. Run `TEST_V1_9.bat`.
2. Run `RETENTION_REVIEW_V1_9.bat`.
3. Enter a UTF-8 narration `.txt` path and a target duration in seconds (default 45).
4. Reports are written to `output\retention_reports\`; a new filename is used for each run.

Command line:
```bat
python src\retention_review.py "C:\path\to\script.txt" --target-seconds 45 --report "output\retention_reports\my_review.json"
```
If the report path already exists, choose another filename; existing reports are not overwritten.

## Important limitations
The module uses phrase and structure heuristics. It cannot predict audience retention, virality, or YouTube performance. The estimated runtime assumes 150 words per minute and may be wrong for the selected voice, pauses, and editing. A PASS is not a fact-check, originality review, or policy approval. Review facts and the final video manually.
