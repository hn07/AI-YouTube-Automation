# V2.4 – Final Video Quality Gate

V2.4 checks the final MP4 produced by V2.3 using FFprobe metadata. It is a separate review step and does not change the V2.3 renderer, upload registry, or YouTube uploader.

## Checks performed

- Video file exists and is readable by FFprobe.
- Duration is within 30–60 seconds, matching the current V1/V2.3 Short renderer.
- A video stream exists and has 1080×1920 vertical resolution.
- Video codec is H.264; a different codec triggers REVIEW.
- An audio stream exists; absence is FAIL.
- Audio codec is AAC; another codec triggers REVIEW.
- File size is at least 100,000 bytes.
- Container is identified as MP4/MOV family.

Overall status:
- PASS: all metadata checks passed.
- REVIEW: no hard failures, but a codec check needs a person to decide.
- FAIL: one or more required checks failed.

## Limitations

This is a metadata and file-sanity check, not a computer-vision quality assessment. It cannot reliably detect every black frame, frozen frame, caption error, inaudible narration, factual error, copyright issue, or YouTube policy problem. PASS does not authorize upload or publication. Watch the full video.

V2.4 never uploads, schedules, publishes, or modifies the publish_allowed field.

## Update safely on Windows 11

Open Command Prompt:

    cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
    git status
    git fetch origin

Back up or commit any local changes before switching. Do not use git reset --hard and do not delete output.

    git switch feature/v2.4-final-video-quality-gate

If the local branch does not exist:

    git switch -c feature/v2.4-final-video-quality-gate --track origin/feature/v2.4-final-video-quality-gate

## Test first

Run:

    TEST_V2_4.bat

Tests use mocked FFprobe data and a temporary dummy file. They do not require FFmpeg, Internet, TTS, or YouTube.

## Check a rendered video

Run:

    FINAL_QUALITY_GATE_V2_4.bat

Choose option 1 and paste the full path to short.mp4, or option 2 and paste the path to V2.3 render_manifest.json.

CLI:

    python src\final_video_quality_v2_4.py "output\rendered_jobs\JOBID_timestamp\short.mp4"

or:

    python src\final_video_quality_v2_4.py "output\rendered_jobs\JOBID_timestamp\render_manifest.json"

The tool locates ffprobe.exe from tools\ffmpeg\bin or PATH. If necessary, pass --ffprobe "C:\path\to\ffprobe.exe".

A JSON report is saved beside the video with a timestamped name. If you supply --report, an existing report path is never overwritten.

## Recommended final workflow

1. Run V2.3 and produce the MP4.
2. Run V2.4 and review all findings.
3. Open and watch the entire MP4 with sound. Check the first and last seconds, captions, voice clarity, factual claims, and rights.
4. Fix issues and render a new output rather than overwriting the prior artifact.
5. Upload only through a separate, deliberate workflow after the human review.

V2.4 does not automatically connect a PASS result to the upload system.
