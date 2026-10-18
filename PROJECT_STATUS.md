# AI YouTube Automation — Project Status

Last updated: 2026-10-18

## Repository

- Repository: https://github.com/hn07/AI-YouTube-Automation
- Default branch: `main`
- Current web UI proposal branch: `feature/web-control-center-ui`
- UI-only pull request: https://github.com/hn07/AI-YouTube-Automation/pull/2

## Version tracks currently present on GitHub

The repository has separate feature branches for the development stages below. They are not all merged into `main`; use the branch links to inspect each stage.

- V1 — initial Windows/Streamlit starter
- V1.1 — `feature/v1.1-batch-workflow`
- V1.2 — `feature/v1.2-reliable-render-upload`
- V1.3 — `feature/v1.3-daily-auto-schedule` and `feature/v1.3-daily-auto-scheduler`
- V1.4 — `feature/v1.4-reliable-automation`
- V1.5 — `feature/v1.5-ai-script-provider`
- V1.6 — `feature/v1.6-topic-research`
- V1.7 — `feature/v1.7-video-dashboard`
- V1.8 — `feature/v1.8-content-quality`
- V1.9 — `feature/v1.9-shorts-retention-check`
- V2.0 — `feature/v2.0-production-pipeline`
- V2.1 — `feature/v2.1-ai-script-research`
- V2.2 — `feature/v2.2-fact-check-sources`
- V2.3 — `feature/v2.3-video-rendering-integration`
- V2.4 — `feature/v2.4-final-video-quality-gate`
- V2.5 — `feature/v2.5-one-click-auto-production`

## Current job being debugged

- Job ID: `20261018_165128_af84e9`
- Topic: `Creepy Facts About the Ocean`
- Script on the user's Windows PC: `D:\\MyWorkSpace\\AI_YouTube_Automation_V1_1\\ocean_script.txt`
- Current local V2.2 register: `output/fact_check/20261018_165128_af84e9_claims.json`
- Latest local V2.2 report mentioned in the conversation: `output/fact_check/20261018_165128_af84e9_fact_check_report_20261018_181207.json`
- Latest V2.2 output: `NEEDS_HUMAN_REVIEW`; counts showed 7 Verified, but the register's `reviewed_by` field is blank and reviewer notes still require source checking. V2.2 validates human-review record fields and URL formatting; it does not independently verify factual truth.
- V2.5 run mentioned in the conversation: `output/v2_5_runs/20261018_165128_af84e9_v2_5_20261018_180046.json`
- V2.5 result: `BLOCKED`. Human approval is not recorded and the latest V2.2 status is not `HUMAN_REVIEW_COMPLETE`.
- Upload and publishing remain disabled.

## Work completed in this conversation

1. Reviewed the current V2.2 claim register and identified that a URL alone does not prove a claim.
2. Rewrote the seven ocean-topic claims to improve accuracy and added primary NOAA source URLs where relevant.
3. Identified that the register still requires genuine human source review; no human approval should be fabricated.
4. Added a proposed GitHub web control center:
   - `docs/index.html` — browser-based project links
   - `.github/workflows/web-control-center.yml` — GitHub Actions form for creating a draft script/evidence-review package
   - `WEB_CONTROL_CENTER_GUIDE.md` — operating guide
5. This UI addition is in a pull request and has not been merged into `main`.

## What the new web workflow does and does not do

It lets the user submit a topic and script through GitHub's web interface and download a draft package artifact. Claims begin as `UNREVIEWED`.

It does **not** run the full Windows-local pipeline, read files from the user's PC, independently fact-check claims, render a finished MP4, or upload/schedule/publish a video.

## Next steps from the browser

1. Review and merge the UI-only PR: https://github.com/hn07/AI-YouTube-Automation/pull/2
2. In repository **Actions**, run **Web Control Center - YouTube Shorts** to create a draft review package.
3. In **Settings → Pages**, select branch `main` and folder `/docs` to publish the control-center page.
4. Continue the V2.2 code fix in its feature branch after reviewing the actual condition that produces `NEEDS_HUMAN_REVIEW`.
5. Only after real evidence review and explicit human approval should a production runner be allowed past its gates.

## Local files and privacy

This status file records paths and statuses provided in the conversation. It does not upload the user's local output folder, OAuth credentials, YouTube tokens, API keys, or private files. Those remain on the user's computer unless the user deliberately uploads them.
