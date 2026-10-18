# Long-form 16:9 Draft Renderer (free-first)

This is a separate workflow. It does not replace or edit the existing Shorts or Web Control Center workflows.

## Run from GitHub web

1. Open the repository: https://github.com/hn07/AI-YouTube-Automation
2. Select **Actions**.
3. Select **Render YouTube Long-Form Draft (Free)** in the left sidebar.
4. Click **Run workflow** and keep branch set to `main`.
5. Enter a concise topic (used for the title overlay and as search context).
6. Paste the reviewed English script. Aim for enough narration for 5–10 minutes (roughly 650–1,400 words depending on speaking speed; use the generated duration as the final check).
7. Choose Aria, Guy, or Jenny and click **Run workflow**.
8. Open the completed run, scroll to **Artifacts**, and download `youtube-long-video-draft-<run number>`.
9. Extract the ZIP and review `youtube_long_draft.mp4`, `scene_image_matches.json`, `image_credits.json`, `captions.srt`, and `REVIEW_BEFORE_USE.txt`.

## What it does

- Creates a 1920×1080 landscape MP4.
- Searches Wikimedia Commons separately for each script sentence using meaningful keywords; the best title-keyword overlap is preferred among returned results.
- Records the sentence, search query, selected image title, source, artist and license metadata in the review files.
- Uses original abstract backgrounds when no downloadable Commons image is found.
- Produces narration, synthesized ambient audio, an SRT subtitle file, and a review checklist.
- Keeps all outputs as a downloadable GitHub Actions artifact (retained for 30 days).

## Important limitations

- Image matching is keyword-based, not semantic AI vision. A human must inspect every scene and confirm the image really fits the sentence.
- Commons metadata and license labels can be incomplete or require attribution. Open each source and verify reuse requirements before publishing.
- Caption timing is estimated from sentence word counts and may not match spoken pauses exactly.
- The workflow warns if narration is outside 5–10 minutes; it does not rewrite or trim the script automatically.
- GitHub-hosted Actions usage and limits depend on the account and repository plan. This design avoids paid AI APIs, but internet access is required to retrieve images and narration.
- **Draft only:** no YouTube API credentials are used; nothing is uploaded, scheduled, or published.

## Existing workflows

- `Render YouTube Short Draft (Free)`: existing vertical 9:16 renderer, unchanged.
- `Web Control Center - YouTube Shorts`: existing script/evidence review package, unchanged.
- `Render YouTube Long-Form Draft (Free)`: new horizontal 16:9 renderer.
