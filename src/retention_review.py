"""V1.9 heuristic retention-structure checks for short-form narration."""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from pathlib import Path

WORD_RE = re.compile(r"\b[\w]+(?:['’-][\w]+)*\b", re.UNICODE)
SENTENCE_RE = re.compile(r"[^.!?]+[.!?]*")
HOOK_CUES = ("imagine", "what if", "did you know", "here's why", "here is why",
             "but then", "until", "at first", "the strange part", "the problem",
             "never", "why", "how", "this is what", "one day", "at exactly")
ENDING_CUES = ("what do you think", "would you", "which one", "comment below",
               "tell me", "follow for", "subscribe", "part two", "part 2",
               "the question is", "and that's why", "but the real question")
GENERIC_HOOKS = ("today we're going to talk about", "in this video", "hello everyone",
                 "welcome back to my channel", "today i will tell you")
FILLER_PHRASES = ("in conclusion", "as we all know", "needless to say",
                  "it is important to note that", "without further ado")

def words(text: str):
    return WORD_RE.findall(text or "")

def sentences(text: str):
    return [re.sub(r"\s+", " ", s).strip() for s in SENTENCE_RE.findall(text or "") if words(s)]

def analyze_retention(script: str, target_seconds: int = 45) -> dict:
    script = (script or "").strip()
    parts, tokens = sentences(script), words(script)
    findings = []
    def add(code, severity, message, suggestion):
        findings.append({"code": code, "severity": severity, "message": message, "suggestion": suggestion})
    if not script:
        add("SCRIPT_EMPTY", "BLOCK", "Script is empty.", "Write the narration before reviewing its structure.")
    else:
        first = " ".join(parts[:2]).lower()
        first_words = len(words(" ".join(parts[:2])))
        if first_words > 0 and first_words > 42:
            add("HOOK_SLOW", "REVIEW", "The opening two sentences contain more than 42 words.", "Try starting with the central mystery, surprising detail, or question.")
        if first_words and not any(cue in first for cue in HOOK_CUES) and not re.search(r"\d", first):
            add("HOOK_CUE_NOT_FOUND", "REVIEW", "No common hook cue or number was detected near the beginning.", "Manually check whether the first line creates curiosity; a hook does not need a specific phrase.")
        if any(phrase in first for phrase in GENERIC_HOOKS):
            add("GENERIC_OPENING", "REVIEW", "The opening resembles a generic introduction.", "Consider starting directly with the story or most interesting fact.")
        if len(parts) < 3 and len(tokens) > 35:
            add("LOW_STRUCTURE", "REVIEW", "The narration has very few sentence breaks.", "Break the narration into clear, speakable beats.")
        long_sentences = [s for s in parts if len(words(s)) > 25]
        if long_sentences:
            add("LONG_SENTENCE", "REVIEW", "{} sentence(s) contain more than 25 words.".format(len(long_sentences)), "Read aloud and split sentences that are hard to follow.")
        short_sentences = [s for s in parts if 0 < len(words(s)) <= 3]
        if len(short_sentences) >= 4:
            add("CHOPPY_PACING", "REVIEW", "Several sentences contain three words or fewer.", "Check whether the rhythm sounds intentional when read aloud.")
        low = script.lower()
        if any(phrase in low for phrase in FILLER_PHRASES):
            add("FILLER_PHRASE", "REVIEW", "A potentially slow filler phrase was detected.", "Remove it if it delays the main point.")
        last = " ".join(parts[-2:]).lower()
        if tokens and not any(cue in last for cue in ENDING_CUES) and not re.search(r"[?]\s*$", last):
            add("ENDING_WEAK_SIGNAL", "REVIEW", "No obvious question, payoff, or continuation cue was detected at the end.", "Check that the final line delivers a payoff or intentionally invites the viewer to think.")
    # A rough narration estimate, not a promise of actual video duration.
    estimated_seconds = round(len(tokens) / 2.5) if tokens else 0
    if target_seconds < 10 or target_seconds > 180:
        add("TARGET_DURATION_RANGE", "REVIEW", "Target duration is outside the supported 10–180 second review range.", "Use a target between 10 and 180 seconds.")
    elif tokens and estimated_seconds > target_seconds * 1.25:
        add("ESTIMATED_RUNTIME_LONG", "REVIEW", "Estimated narration may exceed the target duration.", "Time a real read-through; speaking speed varies.")
    elif tokens and estimated_seconds < target_seconds * 0.45:
        add("ESTIMATED_RUNTIME_SHORT", "REVIEW", "Estimated narration may be much shorter than the target duration.", "Check the actual voice-over timing before rendering.")
    review_count = sum(1 for f in findings if f["severity"] == "REVIEW")
    block_count = sum(1 for f in findings if f["severity"] == "BLOCK")
    return {
        "schema_version": "1.0", "tool_version": "1.9.0",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "word_count": len(tokens), "sentence_count": len(parts),
        "estimated_narration_seconds_at_150_wpm": estimated_seconds,
        "target_seconds": target_seconds,
        "status": "BLOCK" if block_count else ("REVIEW" if review_count else "PASS"),
        "summary": {"block_count": block_count, "review_count": review_count, "finding_count": len(findings)},
        "findings": findings,
        "limitations": [
            "Heuristics cannot measure actual audience retention or predict virality.",
            "Estimated duration uses 150 words per minute and may differ from the actual voice-over.",
            "PASS does not certify factual accuracy, originality, policy compliance, or monetization eligibility.",
            "Review the story, sources, narration, captions, and final edit manually."
        ]
    }

def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description="V1.9 offline Shorts retention-structure review.")
    parser.add_argument("script", help="Path to UTF-8 narration .txt file")
    parser.add_argument("--target-seconds", type=int, default=45)
    parser.add_argument("--report", default="", help="Optional JSON report; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        source = Path(args.script).expanduser()
        if not source.is_file():
            raise FileNotFoundError("Script file not found: {}".format(source))
        result = analyze_retention(source.read_text(encoding="utf-8-sig"), args.target_seconds)
        result["source_file_name"] = source.name
        if args.report:
            destination = Path(args.report).expanduser()
            destination.parent.mkdir(parents=True, exist_ok=True)
            with destination.open("x", encoding="utf-8") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            result["report_path"] = str(destination)
    except (OSError, UnicodeError, ValueError) as exc:
        print("ERROR: {}".format(exc))
        return 2
    print("V1.9 RETENTION REVIEW: {}".format(result["status"]))
    print("Words: {} | Sentences: {} | Estimated narration: {} sec".format(
        result["word_count"], result["sentence_count"], result["estimated_narration_seconds_at_150_wpm"]))
    for finding in result["findings"]:
        print("[{}] {}: {}".format(finding["severity"], finding["code"], finding["message"]))
        print("  Suggestion: {}".format(finding["suggestion"]))
    if result.get("report_path"):
        print("Report saved: {}".format(result["report_path"]))
    print("Heuristic only; manually review the script and final video.")
    return 1 if result["status"] == "BLOCK" else 0

if __name__ == "__main__":
    raise SystemExit(main())
