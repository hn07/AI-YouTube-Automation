# Web Control Center (no CMD)

## What this adds
- A GitHub-hosted control page under `docs/index.html`.
- A manual GitHub Actions form for entering a topic, script, and voice preference.
- A downloadable review package containing the script, metadata, and (optionally) an evidence checklist.
- Claims are initialized as `UNREVIEWED`. The workflow never simulates human review or approval.
- No video rendering, upload, scheduling, or publishing is performed by this workflow.

## Use from the GitHub interface
1. Open the repository's **Actions** tab.
2. Select **Web Control Center - YouTube Shorts**.
3. Click **Run workflow**, fill the form, and start the run.
4. Open the completed run and download its artifact.
5. Review the script and evidence checklist before using any local rendering pipeline.

## Enable the static control page
After this branch is reviewed and merged, open **Settings → Pages** and select **Deploy from a branch**, branch `main`, folder `/docs`. Save. GitHub will show the published URL in Settings → Pages.

## Important limitation
GitHub Pages is a static website and cannot run the local Windows Python/FFmpeg pipeline or access files on your PC. The workflow in this change creates a draft review package on GitHub-hosted runners. The existing V2.5 production runner requires job files and evidence/approval gates; this change deliberately does not bypass those gates. Publishing is not included.
