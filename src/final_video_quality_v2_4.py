"""V2.4 final MP4 metadata quality gate. Offline tests can inject ffprobe results."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
MIN_BYTES = 100_000
MIN_SECONDS = 30.0
MAX_SECONDS = 60.0
EXPECTED_WIDTH = 1080
EXPECTED_HEIGHT = 1920


def find_ffprobe(explicit: Optional[str] = None) -> str:
    if explicit:
        path = Path(explicit).expanduser()
        if path.is_file():
            return str(path.resolve())
        located = shutil.which(explicit)
        if located:
            return located
        raise FileNotFoundError("ffprobe executable not found: {}".format(explicit))
    bundled = ROOT / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"
    if bundled.is_file():
        return str(bundled.resolve())
    located = shutil.which("ffprobe")
    if located:
        return located
    raise FileNotFoundError("ffprobe not found. Install the full FFmpeg build or pass --ffprobe.")


def _probe(video: Path, ffprobe: str) -> dict:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries",
         "format=duration,format_name,size:stream=codec_type,codec_name,width,height",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        detail = (result.stderr or "ffprobe returned an error").strip()[-1200:]
        raise RuntimeError("ffprobe could not read the MP4: " + detail)
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned invalid JSON.") from exc
    if not isinstance(data, dict):
        raise RuntimeError("ffprobe returned an unexpected data structure.")
    return data


def evaluate_video(video_path: str | Path, probe_data: dict, file_size: Optional[int] = None) -> dict:
    video = Path(video_path).expanduser()
    findings = []
    checks = []

    def add(code: str, status: str, message: str, actual=None, expected=None):
        item = {"code": code, "status": status, "message": message}
        if actual is not None:
            item["actual"] = actual
        if expected is not None:
            item["expected"] = expected
        findings.append(item)
        checks.append(status)

    fmt = probe_data.get("format") if isinstance(probe_data.get("format"), dict) else {}
    streams = probe_data.get("streams")
    if not isinstance(streams, list):
        streams = []
    video_streams = [s for s in streams if isinstance(s, dict) and s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if isinstance(s, dict) and s.get("codec_type") == "audio"]

    try:
        duration = float(fmt.get("duration"))
    except (TypeError, ValueError):
        duration = None
    if duration is None:
        add("DURATION_MISSING", "FAIL", "Could not read video duration.")
    elif MIN_SECONDS <= duration <= MAX_SECONDS:
        add("DURATION_RANGE", "PASS", "Duration is within the existing Shorts renderer range.", round(duration, 2), "30–60 seconds")
    else:
        add("DURATION_RANGE", "FAIL", "Duration is outside the expected 30–60 second range.", round(duration, 2), "30–60 seconds")

    if not video_streams:
        add("VIDEO_STREAM_MISSING", "FAIL", "No video stream was detected.")
    else:
        stream = video_streams[0]
        width, height = stream.get("width"), stream.get("height")
        if width == EXPECTED_WIDTH and height == EXPECTED_HEIGHT:
            add("RESOLUTION", "PASS", "Video has the expected vertical resolution.", "{}x{}".format(width, height), "1080x1920")
        else:
            add("RESOLUTION", "FAIL", "Video resolution does not match the expected vertical Shorts format.",
                "{}x{}".format(width, height), "1080x1920")
        codec = str(stream.get("codec_name") or "").lower()
        if codec == "h264":
            add("VIDEO_CODEC", "PASS", "Video codec is H.264.", codec, "h264")
        else:
            add("VIDEO_CODEC", "REVIEW", "Video codec is not the expected H.264 codec.", codec or "unknown", "h264")

    if audio_streams:
        add("AUDIO_STREAM", "PASS", "At least one audio stream was detected.", len(audio_streams), "at least 1")
        audio_codec = str(audio_streams[0].get("codec_name") or "").lower()
        if audio_codec == "aac":
            add("AUDIO_CODEC", "PASS", "Audio codec is AAC.", audio_codec, "aac")
        else:
            add("AUDIO_CODEC", "REVIEW", "Audio is present but not encoded as AAC.", audio_codec or "unknown", "aac")
    else:
        add("AUDIO_STREAM", "FAIL", "No audio stream was detected.")

    try:
        size = int(file_size if file_size is not None else fmt.get("size"))
    except (TypeError, ValueError):
        size = 0
    if size >= MIN_BYTES:
        add("FILE_SIZE", "PASS", "File size is above the minimum sanity threshold.", size, "at least {} bytes".format(MIN_BYTES))
    else:
        add("FILE_SIZE", "FAIL", "File is missing, empty, or suspiciously small.", size, "at least {} bytes".format(MIN_BYTES))

    format_name = str(fmt.get("format_name") or "").lower()
    if "mp4" in format_name or "mov" in format_name:
        add("CONTAINER", "PASS", "Container is compatible with MP4/MOV family.", format_name, "mp4/mov")
    else:
        add("CONTAINER", "FAIL", "Container was not identified as MP4/MOV.", format_name or "unknown", "mp4/mov")

    statuses = {item["status"] for item in findings}
    overall = "FAIL" if "FAIL" in statuses else ("REVIEW" if "REVIEW" in statuses else "PASS")
    return {
        "schema_version": "2.4",
        "tool": "final_video_quality_gate",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "video_path": str(video.resolve()),
        "file_size_bytes": size,
        "duration_seconds": round(duration, 2) if duration is not None else None,
        "status": overall,
        "summary": {
            "pass_count": sum(1 for x in findings if x["status"] == "PASS"),
            "review_count": sum(1 for x in findings if x["status"] == "REVIEW"),
            "fail_count": sum(1 for x in findings if x["status"] == "FAIL"),
        },
        "findings": findings,
        "limitations": [
            "This is a metadata and file-sanity gate; it does not watch the video or judge visual quality.",
            "It does not detect every black frame, frozen frame, bad caption, incorrect fact, copyright issue, or policy violation.",
            "PASS is not permission to upload or publish. A human must watch the full video.",
            "No upload or publishing action is performed."
        ]
    }


def save_report(report: dict, destination: Optional[str | Path] = None) -> Path:
    video = Path(report["video_path"])
    if destination:
        path = Path(destination).expanduser()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = video.parent / ("final_quality_report_" + stamp + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return path


def check_video(video_path: str | Path, ffprobe_path: Optional[str] = None) -> dict:
    video = Path(video_path).expanduser()
    if not video.is_file():
        raise FileNotFoundError("Video file not found: {}".format(video))
    probe = _probe(video, find_ffprobe(ffprobe_path))
    return evaluate_video(video, probe, video.stat().st_size)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="V2.4 final MP4 metadata quality gate. Never uploads.")
    parser.add_argument("video", help="Path to rendered MP4 or V2.3 render manifest JSON")
    parser.add_argument("--ffprobe", default="", help="Optional full path to ffprobe.exe")
    parser.add_argument("--report", default="", help="Optional report path; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        source = Path(args.video).expanduser()
        if not source.is_file():
            raise FileNotFoundError("Input file not found: {}".format(source))
        if source.suffix.lower() == ".json":
            manifest = json.loads(source.read_text(encoding="utf-8-sig"))
            if not isinstance(manifest, dict) or not manifest.get("video_path"):
                raise ValueError("JSON input must be a V2.3 render_manifest.json with video_path.")
            video = Path(manifest["video_path"]).expanduser()
            if not video.is_absolute():
                video = source.parent / video
        else:
            video = source
        report = check_video(video, args.ffprobe or None)
        report_path = save_report(report, args.report or None)
        print("V2.4 FINAL VIDEO QUALITY: {}".format(report["status"]))
        print("Video: {}".format(report["video_path"]))
        print("Duration: {} | Size: {} bytes".format(report["duration_seconds"], report["file_size_bytes"]))
        for item in report["findings"]:
            print("[{}] {}: {}".format(item["status"], item["code"], item["message"]))
        print("Report: {}".format(report_path.resolve()))
        print("Metadata checks only. Watch the full video; no upload or publishing was performed.")
        return 1 if report["status"] == "FAIL" else 0
    except (OSError, UnicodeError, ValueError, RuntimeError, TypeError, json.JSONDecodeError) as exc:
        print("ERROR: {}".format(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
