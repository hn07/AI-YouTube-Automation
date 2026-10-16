import asyncio
import logging
import re
import shutil
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

log = logging.getLogger("ytauto")

def find_ffmpeg() -> str | None:
    local = Path("tools/ffmpeg/bin/ffmpeg.exe")
    return str(local.resolve()) if local.exists() else shutil.which("ffmpeg")

def choose_font(size=54):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\Arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                pass
    return ImageFont.load_default()

def wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, line = [], ""
    for word in words:
        trial = (line + " " + word).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            line = trial
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def make_background(text: str, path: Path):
    # Original, locally generated abstract background; no stock-media rights required.
    w, h = 1080, 1920
    img = Image.new("RGB", (w, h), (13, 23, 42))
    pix = img.load()
    for y in range(h):
        for x in range(w):
            # subtle blue/purple gradient
            pix[x, y] = (13 + int(15*x/w), 23 + int(8*y/h), 42 + int(32*x/w))
    d = ImageDraw.Draw(img)
    d.ellipse((720, 100, 1250, 650), fill=(35, 61, 105))
    d.ellipse((-220, 1350, 420, 1990), fill=(36, 49, 92))
    title = re.sub(r"\s+", " ", text).strip()
    if len(title) > 85:
        title = title[:82].rsplit(" ", 1)[0] + "..."
    font = choose_font(68)
    lines = wrap_text(d, title.upper(), font, 850)
    line_h = 92
    y = (h - len(lines)*line_h)//2 - 30
    for line in lines:
        bbox = d.textbbox((0,0), line, font=font, stroke_width=1)
        x = (w - (bbox[2]-bbox[0]))//2
        d.text((x+3,y+4), line, font=font, fill=(0,0,0), stroke_width=2, stroke_fill=(0,0,0))
        d.text((x,y), line, font=font, fill=(255,255,255), stroke_width=1, stroke_fill=(120,190,255))
        y += line_h
    d.text((70, 1700), "QUICK EXPLAINER  •  CHECK THE FACTS", font=choose_font(30), fill=(190,210,240))
    img.save(path, quality=92)

async def create_voice(text: str, out_mp3: Path, voice="en-US-AriaNeural"):
    communicate = edge_tts.Communicate(text=text, voice=voice, rate="+0%", volume="+0%")
    await communicate.save(str(out_mp3))

def make_srt(script: str, duration: float, out_srt: Path):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script.strip()) if s.strip()]
    if not sentences:
        sentences = [script.strip()]
    weights = [max(1, len(s.split())) for s in sentences]
    total = sum(weights)
    t = 0.0
    def stamp(seconds):
        ms = int(round(seconds*1000))
        hh, rem = divmod(ms, 3600000)
        mm, rem = divmod(rem, 60000)
        ss, milli = divmod(rem, 1000)
        return f"{hh:02}:{mm:02}:{ss:02},{milli:03}"
    chunks = []
    for i, (sentence, weight) in enumerate(zip(sentences, weights), 1):
        end = duration if i == len(sentences) else t + duration*weight/total
        chunks.append(f"{i}\n{stamp(t)} --> {stamp(end)}\n{sentence}\n")
        t = end
    out_srt.write_text("\n".join(chunks), encoding="utf-8")

def probe_duration(ffmpeg: str, media: Path) -> float:
    # ffprobe usually ships alongside ffmpeg.
    ffprobe = str(Path(ffmpeg).with_name("ffprobe.exe")) if ffmpeg.lower().endswith(".exe") else shutil.which("ffprobe")
    if not ffprobe or not Path(ffprobe).exists():
        ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found. Install the full FFmpeg build (ffmpeg + ffprobe).")
    result = subprocess.run([ffprobe, "-v", "error", "-show_entries", "format=duration",
                             "-of", "default=noprint_wrappers=1:nokey=1", str(media)],
                            capture_output=True, text=True, check=True)
    return float(result.stdout.strip())

def _shorten_script(script: str, target_words: int) -> str:
    """Reduce narration conservatively while keeping sentence boundaries where possible."""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script.strip()) if s.strip()]
    kept = []
    count = 0
    for sentence in sentences:
        words = sentence.split()
        if count + len(words) <= target_words:
            kept.append(sentence)
            count += len(words)
        elif not kept:
            kept.append(" ".join(words[:target_words]).rstrip(",;:") + ".")
            break
        else:
            break
    return " ".join(kept).strip()


def _run_ffmpeg(cmd: list[str], stage: str) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"{stage} failed: {result.stderr[-1800:]}")


def _validate_mp4(ffmpeg: str, mp4: Path) -> float:
    if not mp4.exists() or mp4.stat().st_size < 100_000:
        raise RuntimeError("Quality check failed: output missing or suspiciously small.")
    duration = probe_duration(ffmpeg, mp4)
    if not 30 <= duration <= 60:
        raise RuntimeError(f"Quality check failed: final duration {duration:.1f}s outside 30–60s.")
    ffprobe = str(Path(ffmpeg).with_name("ffprobe.exe")) if ffmpeg.lower().endswith(".exe") else shutil.which("ffprobe")
    if not ffprobe or not Path(ffprobe).exists():
        ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found; cannot validate the finished MP4.")
    probe = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,codec_name",
         "-of", "default=noprint_wrappers=1", str(mp4)],
        capture_output=True, text=True
    )
    if probe.returncode != 0 or "width=1080" not in probe.stdout or "height=1920" not in probe.stdout:
        raise RuntimeError("Quality check failed: expected a readable 1080x1920 vertical video. " + probe.stderr[-500:])
    return duration


def render_short(topic: str, script: str, output_dir: Path, voice="en-US-AriaNeural"):
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        raise RuntimeError("FFmpeg not found. Install it and add its bin folder to PATH, then restart this app.")
    output_dir.mkdir(parents=True, exist_ok=True)
    work = output_dir / "_work"
    work.mkdir(exist_ok=True)
    bg, audio, srt = work/"background.png", work/"voice.mp3", work/"captions.srt"
    mp4 = output_dir / "short.mp4"
    make_background(topic, bg)

    # Up to three total attempts; each failed duration attempt shortens the script.
    current_script = script.strip()
    last_duration = None
    for attempt in range(3):
        asyncio.run(create_voice(current_script, audio, voice))
        # Render narration first so ffprobe can measure the real audio/video duration.
        raw = output_dir / "short_raw.mp4"
        cmd = [ffmpeg, "-y", "-loop", "1", "-i", str(bg), "-i", str(audio),
               "-c:v", "libx264", "-tune", "stillimage", "-c:a", "aac", "-b:a", "160k",
               "-pix_fmt", "yuv420p", "-shortest", "-vf", "scale=1080:1920,fps=30",
               "-movflags", "+faststart", str(raw)]
        _run_ffmpeg(cmd, "Initial FFmpeg render")
        last_duration = probe_duration(ffmpeg, raw)
        if 30 <= last_duration <= 60:
            raw.replace(mp4)
            break
        if attempt == 2:
            raise RuntimeError(
                f"Voice duration remained {last_duration:.1f}s after 3 attempts. "
                "Please edit the narration manually and retry."
            )
        if last_duration > 60:
            ratio = 54.0 / last_duration
            target_words = max(65, int(len(current_script.split()) * ratio))
        else:
            target_words = min(160, max(len(current_script.split()) + 10, int(len(current_script.split()) * 1.2)))
        shortened = _shorten_script(current_script, target_words)
        if shortened == current_script or len(shortened.split()) < 60:
            raise RuntimeError(
                f"Narration duration {last_duration:.1f}s is outside 30–60s and cannot be safely auto-adjusted. "
                "Please edit the script to roughly 75–130 words."
            )
        log.warning("Duration %.1fs outside Shorts range; retry %d/2 with adjusted narration", last_duration, attempt + 1)
        current_script = shortened

    duration = probe_duration(ffmpeg, mp4)
    make_srt(current_script, duration, srt)
    subtitled = output_dir/"short_captioned.mp4"
    escaped_srt = str(srt.resolve()).replace("\\", "/").replace(":", "\\:")
    cmd2 = [ffmpeg, "-y", "-i", str(mp4), "-vf",
            f"subtitles='{escaped_srt}':force_style='FontName=Arial,FontSize=18,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=170'",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-c:a", "copy",
            "-movflags", "+faststart", str(subtitled)]
    result = subprocess.run(cmd2, capture_output=True, text=True)
    if result.returncode == 0 and subtitled.exists() and subtitled.stat().st_size > 100_000:
        subtitled.replace(mp4)
    else:
        log.warning("Caption burn failed; retaining video without burned captions. Details: %s", result.stderr[-1000:])
    final_duration = _validate_mp4(ffmpeg, mp4)
    log.info("V1.2 quality gate passed: path=%s duration=%.2f size=%d", mp4, final_duration, mp4.stat().st_size)
    return mp4, final_duration
