# V1.6 — RSS Topic Research Queue

V1.6 adds an **optional, manual** RSS/Atom discovery workflow on top of V1.5. It does not change the daily runner or automatically publish research topics.

## What it does
- Reads a small default set of public science RSS feeds, or feeds configured in `TOPIC_RSS_FEEDS` (comma-separated HTTPS URLs).
- Extracts headline, source URL, date and short summary where available.
- Deduplicates exact headline+URL pairs against the reviewed-history file.
- Saves a local review queue to `output/researched_topic_candidates.json`.
- Limits feeds, per-feed entries and response size; applies a timeout and rejects redirects to non-HTTPS URLs.
- Uses Python's standard library only.

## Run on Windows
From the existing project folder:

```bat
cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
git status
git fetch origin
git switch feature/v1.6-topic-research
TEST_V1_6.bat
RESEARCH_TOPICS_V1_6.bat
```

If the local branch does not exist:

```bat
git switch -c feature/v1.6-topic-research --track origin/feature/v1.6-topic-research
```

If `git status` shows local changes, do not reset or clean them; review them before switching branches.

## Output
- `output/researched_topic_candidates.json`: newly discovered candidates and source links.
- `output/researched_topic_history.json`: topics explicitly marked reviewed by a future review workflow.

## Important limitations
- RSS headlines are discovery leads, **not verified facts**. Open source links and verify claims against primary sources before publishing.
- The default daily runner continues using the curated local topic bank; RSS results are not automatically fed into rendering or upload.
- The first run may have no candidates if the feeds are unavailable or all items were previously reviewed. Feed access depends on Internet availability and publisher RSS uptime.
- Neither test nor research runner renders a video or uploads to YouTube.
- This is a GitHub branch update and must be tested on the user's Windows machine; no local test result is implied.
