# V2.5 One-Click Local Production (Preview)

## Files
- `RUN_V2_5_ONE_CLICK.bat`: asks for an existing job ID and runs the orchestrator.
- `TEST_V2_5.bat`: syntax smoke test.
- `src/one_click_production_v2_5.py`: preflight and gated rendering coordinator.

## Safety
V2.5 does not create fake source verification or human approval, does not overwrite existing reports, and never uploads, schedules, or publishes. It runs the existing V2.3 renderer only if the job already has passing V2.0 quality/retention checks, explicit human approval, and a latest V2.2 fact-check run marked `HUMAN_REVIEW_COMPLETE` with every claim marked `VERIFIED`. A source URL alone is not proof that a claim is true.

After rendering, the existing V2.4 metadata gate checks file/container/codec/resolution/duration/audio. This is not a visual or factual review. Watch the complete MP4 yourself before any separate upload workflow.

## Run
1. Back up important project files as a general precaution; V2.5 itself does not delete outputs.
2. Copy/merge these V2.5 files into your existing project folder without replacing your existing data.
3. Run `TEST_V2_5.bat`.
4. Run `RUN_V2_5_ONE_CLICK.bat` and enter an existing job ID.
5. Read the blocker list and the JSON report under `output/v2_5_runs`.

If a job is not eligible, V2.5 stops and writes a report rather than bypassing the checks. The current Ocean topic job's claims were previously recorded as UNREVIEWED, so it is expected to stop until those claims are genuinely reviewed.

## Known limitations
- The runner does not yet automatically search the web or independently validate factual claims.
- V2.4 checks metadata only, not black frames, caption timing, factual truth, copyright, or whether narration sounds good.
- Rendering uses the project's existing Edge TTS integration and needs Internet access.
- This branch is a preview and has not been run on your Windows machine. The smoke test must be executed locally before production use.
