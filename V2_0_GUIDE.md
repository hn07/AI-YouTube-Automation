# V2.0 – AI YouTube Production Pipeline

V2.0 adds a local job ledger connecting the V1.8 content-quality check and V1.9 retention-structure review into one traceable workflow.

## Safety and scope

- Uses Python standard library plus the existing src/content_quality.py and src/retention_review.py.
- Offline operation: no AI APIs, RSS feeds, YouTube, or other network services.
- Does not render videos, schedule them, upload them, or publish them.
- Creates unique job records and refuses to overwrite existing review reports.
- Approval is a manual decision only. publish_allowed remains false.
- Checks are heuristic only. PASS is not a fact-check, copyright check, or guarantee of retention.

## Files added

- src/production_pipeline.py – create/list/check/approve job CLI.
- PIPELINE_V2_0.bat – interactive Windows menu.
- TEST_V2_0.bat – offline smoke tests.
- V2_0_GUIDE.md – this guide.

## Install/update safely on Windows

From Command Prompt:

    cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
    git status
    git fetch origin
    git switch feature/v2.0-production-pipeline

If the local branch does not exist:

    git switch -c feature/v2.0-production-pipeline --track origin/feature/v2.0-production-pipeline

If git status shows modified/untracked work, do not discard it. Commit or back it up before switching branches. Do not use git reset --hard.

## Run the test

Double-click TEST_V2_0.bat, or run it from Command Prompt. It only performs local smoke tests.

## Create a job

Run PIPELINE_V2_0.bat and choose option 1, or run:

    python src\production_pipeline.py new --topic "Creepy Facts About the Ocean" --title "Creepy Facts About the Ocean" --target-seconds 45

A new JSON record is created under output\pipeline_jobs. Open that JSON in a text editor and fill description and script_path. script_path can be an absolute path or a path relative to the project folder. Narration must be a UTF-8 text file.

Example values:

    "description": "Short narration about unusual ocean facts. Check sources before publication.",
    "script_path": "scripts\\ocean_short.txt"

## Run combined checks

Copy job_id from the JSON filename (without .json), then run:

    python src\production_pipeline.py check YOUR_JOB_ID

The command runs V1.8 content checks and V1.9 retention review, writes two JSON reports to output\pipeline_reports, and updates the job status. It refuses to overwrite reports with the same job ID; archive existing reports before intentionally rerunning.

Possible states:

- topic_selected: job created, checks not run.
- needs_human_review: neither check returned BLOCK; human review and fact-check still required.
- blocked: at least one check returned BLOCK.
- human_approved: a human approval note was recorded after checks.

REVIEW results are warnings, not proof that a script is wrong or right. Verify factual claims from trustworthy sources.

## Record human approval

After reviewing both reports and fact-checking the script:

    python src\production_pipeline.py approve YOUR_JOB_ID --note "Reviewed script and checked factual sources manually."

Approval is refused if either check is BLOCK or has not been run. Approval does not enable upload/publishing. V2.0 intentionally stops before rendering and publishing.

## List jobs

    python src\production_pipeline.py list

## Troubleshooting

- Script file not found: check script_path in the job JSON.
- No script path set: enter a UTF-8 .txt path in the job JSON.
- Report already exists: archive the old report files before rerunning; existing reports are preserved.
- python is not recognized: use the Python executable from your existing V1.x setup.

## V2.0 workflow

1. Select topic and manually record a source URL.
2. Add title, description, and narration text file.
3. Run combined quality and retention checks.
4. Read findings and fact-check manually.
5. Record manual approval.
6. Stop: rendering and upload remain separate, explicitly controlled steps.
