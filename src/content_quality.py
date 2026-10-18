"""V1.8 offline quality checks for YouTube Shorts scripts."""
from __future__ import annotations
import json, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

WORD_RE = re.compile(r"\b[\w]+(?:['’-][\w]+)*\b", re.UNICODE)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*")
REVIEW_PHRASES = ("100% guaranteed", "guaranteed to", "miracle cure", "scientists confirm", "experts prove", "the shocking truth", "secret they don't want you to know")
CLICKBAIT_PHRASES = ("you won't believe", "shocking", "mind-blowing", "insane", "this will change everything", "the truth they hide")

def _words(text: str) -> List[str]:
    return WORD_RE.findall(text or "")

def check_content(script: str, title: str = "", description: str = "") -> Dict:
    script, title, description = (script or "").strip(), (title or "").strip(), (description or "").strip()
    words, findings = _words(script), []
    blockers, reviews = [], []
    def add(code: str, severity: str, message: str) -> None:
        item = {"code": code, "severity": severity, "message": message}
        findings.append(item)
        (blockers if severity == "BLOCK" else reviews if severity == "REVIEW" else []).append(item) if severity in ("BLOCK", "REVIEW") else None
    if not script:
        add("SCRIPT_EMPTY", "BLOCK", "Narration script is empty.")
    else:
        if len(words) < 70:
            add("SCRIPT_SHORT", "REVIEW", "Script has fewer than 70 words; check whether it has enough substance.")
        elif len(words) > 145:
            add("SCRIPT_LONG", "REVIEW", "Script has more than 145 words; check Shorts pacing and target duration.")
        if len(script) < 250:
            add("SCRIPT_VERY_SHORT", "REVIEW", "Script is under 250 characters.")
        if re.search(r"([!?.,])\1{2,}", script):
            add("PUNCTUATION_EXCESS", "REVIEW", "Repeated punctuation may look spammy.")
        if re.search(r"\b[A-Z]{7,}\b", script):
            add("ALL_CAPS", "REVIEW", "Long all-caps words may sound like shouting.")
        sentences = [re.sub(r"\s+", " ", s).strip().lower() for s in SENTENCE_RE.findall(script)]
        sentences = [s for s in sentences if len(_words(s)) >= 4]
        if len(sentences) != len(set(sentences)):
            add("REPEATED_SENTENCE", "REVIEW", "One or more full sentences are repeated.")
        low = script.lower()
        if any(p in low for p in REVIEW_PHRASES):
            add("CLAIM_REVIEW", "REVIEW", "Potentially absolute or scientific/medical claim detected; verify it against a reliable source.")
        if any(p in low or p in title.lower() for p in CLICKBAIT_PHRASES):
            add("CLICKBAIT_WORDING", "REVIEW", "Possible clickbait wording detected; ensure content delivers what the title promises.")
    if not title:
        add("TITLE_MISSING", "REVIEW", "No title supplied; check title before publishing.")
    elif not 5 <= len(title) <= 70:
        add("TITLE_LENGTH", "REVIEW", "Title is outside the suggested 5–70 character range.")
    if not description:
        add("DESCRIPTION_MISSING", "REVIEW", "No description supplied; check description before publishing.")
    elif len(description) < 30:
        add("DESCRIPTION_SHORT", "REVIEW", "Description is under 30 characters; consider adding useful context.")
    return {"schema_version":"1.0","tool_version":"1.8.0","checked_at_utc":datetime.now(timezone.utc).isoformat(),
      "word_count":len(words),"character_count":len(script),"title":title,"description_character_count":len(description),
      "status":"BLOCK" if blockers else ("REVIEW" if reviews else "PASS"),
      "summary":{"block_count":len(blockers),"review_count":len(reviews),"finding_count":len(findings)},
      "findings":findings,"limitations":["Heuristic only, not a grammar checker or fact-checker.",
      "PASS does not guarantee accuracy, originality, monetization eligibility, or YouTube policy compliance.",
      "REVIEW findings require human judgment; the tool does not rewrite scripts or upload videos."]}

def check_file(script_path: str, title: str = "", description: str = "", report_path: Optional[str] = None) -> Dict:
    source = Path(script_path).expanduser()
    if not source.is_file():
        raise FileNotFoundError("Script file not found: {}".format(source))
    report = check_content(source.read_text(encoding="utf-8-sig"), title, description)
    report["source_file_name"] = source.name
    if report_path:
        dest = Path(report_path).expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        report["report_path"] = str(dest)
    return report

def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Offline V1.8 YouTube Shorts content quality check.")
    parser.add_argument("script", help="Path to a UTF-8 .txt narration script")
    parser.add_argument("--title", default="", help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--report", default="", help="Optional JSON report path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        report = check_file(args.script, args.title, args.description, args.report or None)
    except (OSError, UnicodeError, ValueError) as exc:
        print("ERROR: {}".format(exc))
        return 2
    print("V1.8 QUALITY STATUS: {}".format(report["status"]))
    print("Words: {} | Findings: {}".format(report["word_count"], report["summary"]["finding_count"]))
    for item in report["findings"]:
        print("[{}] {}: {}".format(item["severity"], item["code"], item["message"]))
    if report.get("report_path"): print("Report saved: {}".format(report["report_path"]))
    print("Heuristic only; human review and fact-checking are still required.")
    return 1 if report["status"] == "BLOCK" else 0

if __name__ == "__main__":
    raise SystemExit(main())
