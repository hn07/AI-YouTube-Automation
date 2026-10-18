# V2.2 – Fact-Check & Source Verification

V2.2 adds a human evidence register for script claims. It is deliberately not an automatic truth detector.

## What it does

- Reads the script path from an existing production job.
- Splits the script into sentence-sized review items.
- Creates a JSON register with each item marked UNREVIEWED.
- Lets a human add HTTPS source URLs, a review status, reviewer name and a note.
- Validates register structure, status values, HTTPS URL format, and required review notes.
- Writes a separate timestamped report and records the review run in the job JSON.
- Does not overwrite an existing register, approve the job, render video, or upload/publish anything.

## Important limitation

The program does not fetch or read source webpages and cannot determine whether a source is accurate or truly supports a claim. A status of VERIFIED is a human attestation. Read the source itself and compare it with the exact claim. Prefer primary sources and reputable independent corroboration. Do not mark uncertain claims as verified.

## Files

- src/fact_check_v2_2.py – prepare/evaluate CLI.
- src/test_v2_2.py – offline tests.
- FACT_CHECK_V2_2.bat – Windows menu.
- TEST_V2_2.bat – offline smoke tests.

## Safe setup

From Command Prompt:

    cd /d D:\MyWorkSpace\AI_YouTube_Automation_V1_1
    git status
    git fetch origin

Back up or commit uncommitted changes before switching branches. Do not run git reset --hard or delete output folders.

    git switch feature/v2.2-fact-check-sources

If needed:

    git switch -c feature/v2.2-fact-check-sources --track origin/feature/v2.2-fact-check-sources

Run TEST_V2_2.bat before use. Tests are offline and use temporary folders.

## Use V2.2

Run:

    FACT_CHECK_V2_2.bat

### Option 1 – Prepare a claim checklist

1. Enter an existing Job ID.
2. Leave script path blank to use the job's script_path, or enter the full path to a UTF-8 text script.
3. V2.2 writes output\fact_check\<JOB_ID>_claims.json.
4. Open this JSON in a text editor and fill in:
   - top-level reviewed_by: your name or reviewer role.
   - each claim status: VERIFIED, UNCERTAIN, UNSUPPORTED, or UNREVIEWED.
   - each claim source_urls: list of full HTTPS source URLs.
   - each claim reviewer_note: explain how the source supports the exact wording.
5. Save UTF-8 JSON. Do not delete claims simply to make the status pass; retain questionable claims and mark them honestly.

Example:

    {
      "claim_id": "C001",
      "claim_text": "A claim from the script.",
      "status": "VERIFIED",
      "source_urls": ["https://example.org/relevant-primary-source"],
      "reviewer_note": "Read the cited source; it supports the specific claim in context."
    }

This example illustrates the format only. example.org is not evidence for your real script.

### Option 2 – Evaluate the register

1. Choose option 2.
2. Enter the same Job ID.
3. Leave register path blank to use the default register, or enter the exact JSON path.
4. Read the report path and findings.

Possible outcomes:
- HUMAN_REVIEW_COMPLETE: all register items are marked VERIFIED and the required fields/URL formats are present. This does not independently prove truth.
- NEEDS_HUMAN_REVIEW: at least one claim remains unreviewed, uncertain, unsupported, or missing required evidence/notes.

The report is written to output\fact_check\<JOB_ID>_fact_check_report_<timestamp>.json. Each run uses a new report file. The job remains unapproved and publishing remains disabled.

## Suggested workflow with the existing pipeline

1. Create or draft a script with V2.0/V2.1.
2. Run V2.2 option 1 to create a claim register.
3. Open each source and verify the claim manually. Use reliable primary sources when possible.
4. Fill the register and run option 2.
5. Fix or remove unsupported claims in the script; create a new job or a new version of the script and preserve the old artifacts.
6. Run V2.0 quality/retention checks. Existing V2.0 reports are not overwritten; archive them before a rerun or use a new job for a fresh review cycle.
7. Make the human approval decision only after checking the actual content and evidence.

## No automatic publishing

V2.2 never uploads, schedules, or publishes a video. It does not mark human_approved true or publish_allowed true.
