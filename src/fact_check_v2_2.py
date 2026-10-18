"""V2.2 evidence register for human fact-checking; no web claims or publishing."""
from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,79}$")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")


def _stamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_job(job_id: str, root: Path) -> tuple[dict, Path]:
    if not JOB_ID_RE.fullmatch(job_id or ""):
        raise ValueError("Invalid job ID.")
    path = root / "output" / "pipeline_jobs" / (job_id + ".json")
    if not path.is_file():
        raise FileNotFoundError("Job not found: {}".format(path))
    with path.open("r", encoding="utf-8-sig") as stream:
        job = json.load(stream)
    if job.get("job_id") != job_id:
        raise ValueError("Job ID does not match job file.")
    return job, path


def _atomic_json(path: Path, data: dict, exclusive: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if exclusive and path.exists():
        raise FileExistsError("File already exists; refusing to overwrite: {}".format(path))
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temp.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        if exclusive and path.exists():
            raise FileExistsError("File already exists; refusing to overwrite: {}".format(path))
        temp.replace(path)
    finally:
        try:
            temp.unlink(missing_ok=True)
        except OSError:
            pass


def _script_path(job: dict, root: Path, override: str = "") -> Path:
    value = (override or job.get("script_path") or "").strip()
    if not value:
        raise ValueError("No script_path set. Create/select a UTF-8 .txt script first.")
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise FileNotFoundError("Script file not found: {}".format(path))
    return path


def _sentences(script: str) -> list[str]:
    result = []
    for piece in SENTENCE_SPLIT.split(script.strip()):
        clean = re.sub(r"\s+", " ", piece).strip(" \t\r\n-•")
        if len(clean) >= 18:
            result.append(clean)
    return result


def prepare_register(job_id: str, script_path: str = "", root: Optional[Path] = None) -> dict:
    root = Path(root or ROOT).resolve()
    job, _ = _load_job(job_id, root)
    path = _script_path(job, root, script_path)
    text = path.read_text(encoding="utf-8-sig")
    if not text.strip():
        raise ValueError("Script is empty.")
    sentences = _sentences(text)
    if not sentences:
        raise ValueError("No sentence-sized statements found in script.")
    register_path = root / "output" / "fact_check" / (job_id + "_claims.json")
    if register_path.exists():
        raise FileExistsError("Register already exists; refusing to overwrite: {}".format(register_path))
    claims = []
    for index, sentence in enumerate(sentences, 1):
        claims.append({
            "claim_id": "C{:03d}".format(index),
            "claim_text": sentence,
            "status": "UNREVIEWED",
            "source_urls": [],
            "reviewer_note": ""
        })
    register = {
        "schema_version": "2.2",
        "job_id": job_id,
        "topic": job.get("topic", ""),
        "script_path": str(path),
        "created_at_utc": _stamp(),
        "reviewed_by": "",
        "claims": claims,
        "instructions": [
            "This is a review checklist, not an automated fact-check.",
            "Read the linked source itself and confirm it supports the exact claim.",
            "Prefer primary sources and reputable independent sources.",
            "Use VERIFIED only after a human checks the evidence; use UNCERTAIN or UNSUPPORTED honestly.",
            "Do not treat an HTTPS URL, a search snippet, or an AI answer as proof."
        ]
    }
    _atomic_json(register_path, register, exclusive=True)
    return {"path": register_path, "count": len(claims), "register": register}


def _validate_source_url(value: str) -> bool:
    try:
        parsed = urlparse(value.strip())
        return parsed.scheme == "https" and bool(parsed.netloc) and not parsed.username and not parsed.password
    except Exception:
        return False


def evaluate_register(job_id: str, register_path: str = "", root: Optional[Path] = None) -> dict:
    root = Path(root or ROOT).resolve()
    job, job_path = _load_job(job_id, root)
    source = Path(register_path).expanduser() if register_path else root / "output" / "fact_check" / (job_id + "_claims.json")
    if not source.is_absolute():
        source = root / source
    if not source.is_file():
        raise FileNotFoundError("Fact-check register not found: {}".format(source))
    with source.open("r", encoding="utf-8-sig") as stream:
        register = json.load(stream)
    if register.get("job_id") != job_id:
        raise ValueError("Register job_id does not match requested job.")
    claims = register.get("claims")
    if not isinstance(claims, list) or not claims:
        raise ValueError("Register must contain a non-empty claims list.")

    findings = []
    counts = {"VERIFIED": 0, "UNCERTAIN": 0, "UNSUPPORTED": 0, "UNREVIEWED": 0, "INVALID": 0}
    for index, claim in enumerate(claims, 1):
        if not isinstance(claim, dict):
            findings.append({"claim_id": "C{:03d}".format(index), "status": "INVALID", "issues": ["Claim entry is not an object."]})
            counts["INVALID"] += 1
            continue
        claim_id = str(claim.get("claim_id") or "C{:03d}".format(index))
        status = str(claim.get("status") or "UNREVIEWED").strip().upper()
        issues = []
        if not str(claim.get("claim_text") or "").strip():
            issues.append("Claim text is empty.")
        if status not in ("VERIFIED", "UNCERTAIN", "UNSUPPORTED", "UNREVIEWED"):
            issues.append("Unknown status; use VERIFIED, UNCERTAIN, UNSUPPORTED, or UNREVIEWED.")
            status = "INVALID"
        urls = claim.get("source_urls", [])
        if not isinstance(urls, list):
            urls = []
            issues.append("source_urls must be a list.")
        valid_urls = [u.strip() for u in urls if isinstance(u, str) and _validate_source_url(u)]
        invalid_count = len(urls) - len(valid_urls)
        if invalid_count:
            issues.append("One or more source URLs are invalid; use full HTTPS URLs.")
        note = str(claim.get("reviewer_note") or "").strip()
        if status == "VERIFIED":
            if not valid_urls:
                issues.append("VERIFIED requires at least one valid HTTPS source URL.")
            if not note:
                issues.append("VERIFIED requires a reviewer note explaining how the source supports the claim.")
            if not str(register.get("reviewed_by") or "").strip():
                issues.append("Register reviewed_by must identify the human reviewer.")
        if status in ("UNREVIEWED", "UNCERTAIN", "UNSUPPORTED"):
            issues.append("Claim is not fully verified; human review remains required.")
        counts[status if status in counts else "INVALID"] += 1
        if issues:
            findings.append({"claim_id": claim_id, "status": status, "claim_text": str(claim.get("claim_text", ""))[:400], "issues": issues})
    all_verified = bool(claims) and counts["VERIFIED"] == len(claims) and counts["INVALID"] == 0 and not findings
    report = {
        "schema_version": "2.2",
        "tool_version": "2.2.0",
        "checked_at_utc": _stamp(),
        "job_id": job_id,
        "topic": job.get("topic", ""),
        "register_path": str(source),
        "status": "HUMAN_REVIEW_COMPLETE" if all_verified else "NEEDS_HUMAN_REVIEW",
        "claim_count": len(claims),
        "counts": counts,
        "findings": findings,
        "limitations": [
            "The tool validates register structure and HTTPS URL format only; it does not fetch sources or determine truth.",
            "A VERIFIED status is a human attestation, not an independent machine verification.",
            "Check that each cited source actually supports the exact wording and is current and reputable.",
            "This report does not approve, render, upload, schedule, or publish a video."
        ]
    }
    report_path = root / "output" / "fact_check" / (job_id + "_fact_check_report_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json")
    report["report_path"] = str(report_path)
    _atomic_json(report_path, report, exclusive=True)
    job.setdefault("v2_2_fact_check_runs", []).append({
        "checked_at_utc": report["checked_at_utc"],
        "status": report["status"],
        "report_path": str(report_path),
        "register_path": str(source),
        "claim_count": len(claims)
    })
    job["stage"] = "needs_human_review"
    job["human_approved"] = False
    job["publish_allowed"] = False
    job.setdefault("history", []).append({
        "at_utc": _stamp(),
        "event": "V2_2_FACT_CHECK_REGISTER_EVALUATED",
        "detail": "{}; {} claims; human approval and publishing remain separate.".format(report["status"], len(claims))
    })
    _atomic_json(job_path, job)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.2 human fact-check register. No automatic truth claims or publishing.")
    sub = parser.add_subparsers(dest="command", required=True)
    prep = sub.add_parser("prepare", help="Create a claim checklist from an existing job script.")
    prep.add_argument("job_id")
    prep.add_argument("--script", default="")
    review = sub.add_parser("evaluate", help="Evaluate a human-edited claim register.")
    review.add_argument("job_id")
    review.add_argument("--register", default="")
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            result = prepare_register(args.job_id, args.script)
            print("FACT-CHECK REGISTER CREATED: {}".format(result["path"]))
            print("Claims to review: {}".format(result["count"]))
            print("Edit each claim's status, source_urls, reviewer_note, and register reviewed_by.")
            print("No sources were fetched and no claims were automatically verified.")
            return 0
        report = evaluate_register(args.job_id, args.register)
        print("V2.2 FACT-CHECK STATUS: {}".format(report["status"]))
        print("Claims: {} | Verified: {} | Uncertain: {} | Unsupported: {} | Unreviewed: {} | Invalid: {}".format(
            report["claim_count"], report["counts"]["VERIFIED"], report["counts"]["UNCERTAIN"],
            report["counts"]["UNSUPPORTED"], report["counts"]["UNREVIEWED"], report["counts"]["INVALID"]))
        print("Register: {}".format(report["register_path"]))
        print("Report: {}".format(report["report_path"]))
        print("Machine report: {}".format(report.get("checked_at_utc", "")))
        print("This validates human review records and URL format only; it does not independently verify truth.")
        return 0 if report["status"] == "HUMAN_REVIEW_COMPLETE" else 1
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
