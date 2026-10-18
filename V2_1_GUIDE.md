# V2.1 – AI Script & Research Integration

V2.1 extends V2.0 with two optional tools: RSS topic discovery and script drafting for an existing production job.

## Safety and scope

- No automatic rendering, YouTube upload, scheduling, or publishing.
- RSS headlines and summaries are research leads, not verified facts.
- Local drafting is free and offline, but uses a conservative template rather than a generative AI model.
- The AI provider option calls the configured OpenAI-compatible API and may incur charges depending on the provider.
- AI-written scripts may contain errors. Verify factual claims from primary and reputable sources.
- Existing draft files are never overwritten.
- If a job already has script_path, V2.1 preserves it. The new draft is saved separately and does not silently replace the current script.

## Files

- src/ai_research_integration.py – RSS discovery wrapper and script draft command.
- src/test_v2_1.py – offline tests.
- PIPELINE_V2_1.bat – Windows interactive menu.
- TEST_V2_1.bat – offline test runner.

## Update safely on Windows

Open Command Prompt:

    cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
    git status
    git fetch origin

If the working tree contains modified or untracked files, back them up or commit them before switching. Do not use git reset --hard.

Then switch to the new feature branch:

    git switch feature/v2.1-ai-script-research

If it does not exist locally:

    git switch -c feature/v2.1-ai-script-research --track origin/feature/v2.1-ai-script-research

If your local Git doesn't yet see the remote branch, run git fetch origin and check git branch -r.

## Test first

Double-click TEST_V2_1.bat. The tests use temporary directories and the local provider only. They do not call an AI API or RSS feed.

## Use the menu

Run PIPELINE_V2_1.bat.

### Option 1 – Discover topic leads

- Requires an internet connection.
- Fetches configured RSS feeds (the existing V1.6 defaults are NASA and ScienceDaily).
- Saves the candidate queue to output\researched_topic_candidates.json.
- Review the title, source URL, publication date and source content yourself. A headline alone is not evidence.
- If a feed fails, inspect the feed_errors field in the JSON.

### Option 2 – Create a script draft for an existing job

Enter a job ID shown by V2.0's list command. You can keep the job's topic/title/description by leaving optional prompts blank.

Provider choices:
- local: free, offline template draft. This is not a generative AI model.
- ai: requires AI_API_BASE_URL, AI_API_KEY, and AI_MODEL configured for the existing OpenAI-compatible provider. API usage may cost money. Do not paste API keys into chat or commit them to GitHub.

The script is saved to:

    output\scripts\<JOB_ID>_v2_1_draft.txt

V2.1 records the draft metadata in the job JSON. If script_path was empty, it sets it to the new draft. If script_path already points to an existing script, it preserves that path. Read the console output to see which happened.

### After drafting

1. Open the new .txt file and review it.
2. Verify every factual claim using reliable sources; record source URLs manually.
3. If you want to use the new draft for the V2.0 checks and the job already has an old script_path, back up the job JSON and explicitly update script_path to the new draft path. Do not delete the old script.
4. Ensure the job description is populated.
5. V2.0 writes reports under output\pipeline_reports and refuses to overwrite reports with the same job ID. If reports already exist, archive/copy them first or create a new job for a new review cycle.
6. Read the reports and make the human decision. REVIEW is not proof that a script is bad; PASS is not a fact-check.
7. Only use the existing manual approval command after checking the script and sources.

## Command-line examples

Research:

    python src\ai_research_integration.py research --limit 10

Create a free local draft:

    python src\ai_research_integration.py draft YOUR_JOB_ID --provider local --style curiosity

Create a draft using configured AI API:

    python src\ai_research_integration.py draft YOUR_JOB_ID --provider ai --style story

## Troubleshooting

- Job not found: first create a job in V2.0, and copy its exact ID from the list.
- Draft already exists: the script refuses to overwrite it. Back up/rename the prior draft, or use a new job ID.
- AI provider not configured: choose local, or configure the provider privately in your local environment.
- RSS error: network, feed, or provider may be unavailable. This feature is optional.
- No publishing: V2.1 only creates research leads and text drafts. It does not render or upload video.

## V2.1 workflow

1. Create/list a job in V2.0.
2. Optionally discover RSS topic leads and manually select a topic.
3. Create a local or API-generated script draft.
4. Fact-check and edit the draft.
5. Connect the reviewed script to the job, then run V2.0 quality and retention checks.
6. Manually review findings. Nothing is automatically published.
