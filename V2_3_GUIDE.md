# V2.3 – Video Rendering Integration

V2.3 connects an approved V2.0/V2.2 production job to the existing src/video_maker.py renderer. It does not replace the V1 dashboard or automatically upload videos.

## What it does

- Requires an existing job JSON, a UTF-8 narration script, completed V2.0 quality/retention checks, human approval, and the latest recorded V2.2 review status HUMAN_REVIEW_COMPLETE.
- Requires the script path in the job to match the script path in the V2.2 claim register.
- Requires an explicit --confirm-render flag.
- Calls the existing renderer to generate a vertical 1080×1920 MP4 with narration/captions and basic duration/file checks.
- Writes a separate render_manifest.json, records the render run in the job, and leaves publish_allowed=false.
- Does not upload, schedule, or publish.

## Important prerequisites and costs

- FFmpeg and ffprobe must be installed and available as expected by the existing renderer.
- Python dependencies from the base project are required, especially Pillow and edge-tts.
- Voice generation through edge-tts uses an online Microsoft speech endpoint. It requires Internet and is not fully local; service access and terms can change.
- The renderer targets 30–60 seconds even though V2.0 supports jobs up to 180 seconds. Keep V2.3 jobs within the existing renderer's Shorts range.
- Use only scripts and media you have rights to use. The existing renderer creates an original geometric background; it does not download stock footage.

## Safe update

In Command Prompt:

    cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
    git status
    git fetch origin

Back up or commit uncommitted changes before switching. Do not use git reset --hard or delete output.

    git switch feature/v2.3-video-rendering-integration

If the local branch does not exist:

    git switch -c feature/v2.3-video-rendering-integration --track origin/feature/v2.3-video-rendering-integration

Run TEST_V2_3.bat first. The tests use a fake renderer and do not call FFmpeg, TTS, network, or YouTube.

## Job prerequisites

Before rendering:
1. The job must have a valid script_path.
2. Run V2.0 quality and retention checks and review their JSON reports.
3. Use V2.2 to prepare and evaluate the claims register. All claims must have been human-reviewed with appropriate source URLs and notes.
4. Record V2.0 human approval only after the script and evidence are reviewed. V2.2 evaluation itself intentionally resets human approval to false, so approve after the final fact-check evaluation.
5. Ensure the job's script path is exactly the script recorded in the V2.2 register. If the script changes, make a new job or new review register and repeat the checks.

## Use the menu

Run:

    RENDER_V2_3.bat

1. Choose option 1.
2. Enter the existing Job ID.
3. Type RENDER to confirm local rendering.
4. Choose a voice (Aria is default).
5. Wait for FFmpeg and TTS to finish.

CLI alternative:

    python src\render_pipeline_v2_3.py YOUR_JOB_ID --confirm-render --voice en-US-AriaNeural

## Output

Videos and manifests are stored under:

    output\rendered_jobs\<JOB_ID>_<timestamp>\short.mp4
    output\rendered_jobs\<JOB_ID>_<timestamp>\render_manifest.json

A completed render is marked RENDERED_NEEDS_FINAL_HUMAN_REVIEW. Open and watch the full MP4. Check narration, caption timing/spelling, sound, title, factual accuracy, and rights. A successful render does not mean the video is ready to publish.

## Troubleshooting

- Render blocked by approval: run the V2.0 manual approval workflow after reviewing the latest V2.2 report.
- Fact-check status incomplete: revisit the claim register and evaluate it again; if it reports NEEDS_HUMAN_REVIEW, resolve claims honestly.
- Script mismatch: the script was changed after fact-checking or the paths differ. Review the current script and repeat checks; don't bypass the gate.
- FFmpeg/ffprobe not found: install the full FFmpeg build and ensure both executables are available.
- Edge TTS failure: check Internet access, retry later, or troubleshoot the base renderer.
- Partial files after a render error are retained for debugging; inspect them before retrying.

## Offline tests

Run TEST_V2_3.bat. The tests use a fake renderer, so they validate the workflow gates and manifest without actual rendering.

## No upload

V2.3 does not call the YouTube uploader, does not schedule publishing, and never sets publish_allowed to true.
