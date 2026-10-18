#!/usr/bin/env python3
"""Render a landscape long-form YouTube draft with per-sentence relevant images.
Review-only: this script never uploads, schedules, or publishes to YouTube.
"""
import asyncio, json, os, re, subprocess
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT = Path("render-long-work")
ASSETS = ROOT / "assets"
OUT = Path("rendered-long-draft")
W, H = 1920, 1080
UA = "AI-YouTube-Automation/1.1 (review-only renderer)"
STOPWORDS = set("""a an the and or but if then than so of in on at to for from by with about into over after before during is are was were be been being it its this that these those he she they them his her their you your we our i me my as not no do does did have has had can could will would should may might who what when where why how very more most some any all each other also just only up out there here""".split())

def run(cmd):
    subprocess.run(cmd, check=True)

def font(size, bold=False):
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for p in candidates:
        if p.exists():
            try: return ImageFont.truetype(str(p), size)
            except OSError: pass
    try: return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError: return ImageFont.load_default()

def split_sentences(text):
    parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text.strip()) if x.strip()]
    return parts or [text.strip()]

def keywords(text, limit=7):
    words = re.findall(r"[A-Za-z][A-Za-z'-]{2,}", text.lower())
    picked = []
    for word in words:
        if word not in STOPWORDS and word not in picked:
            picked.append(word)
    return picked[:limit] or words[:limit]

def commons_search(query, limit=8):
    params = {
        "action": "query", "format": "json", "generator": "search",
        "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6,
        "gsrlimit": limit, "prop": "imageinfo", "iiprop": "url|extmetadata",
        "iiurlwidth": 1600
    }
    try:
        response = requests.get("https://commons.wikimedia.org/w/api.php", params=params,
                                headers={"User-Agent": UA}, timeout=25)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print(f"Commons search failed for {query!r}: {exc}")
        return []
    results = []
    for page in ((data.get("query") or {}).get("pages") or {}).values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("thumburl") or info.get("url")
        if not url:
            continue
        meta = info.get("extmetadata") or {}
        def val(key):
            raw = (meta.get(key) or {}).get("value", "")
            return re.sub(r"<[^>]*>", "", raw).strip()
        title = page.get("title", "Untitled")
        results.append({
            "title": title, "url": url, "artist": val("Artist") or "Not listed",
            "license": val("LicenseShortName") or "Check source",
            "credit": val("Credit"),
            "source": "https://commons.wikimedia.org/wiki/" + quote(title.replace(" ", "_"))
        })
    # Prefer file titles that overlap the sentence's meaningful keywords.
    terms = set(re.findall(r"[a-z]{3,}", query.lower())) - STOPWORDS
    def score(item):
        title_terms = set(re.findall(r"[a-z]{3,}", item["title"].lower().replace("_", " ")))
        return len(terms & title_terms)
    return sorted(results, key=score, reverse=True)

def search_for_sentence(sentence, topic, index):
    terms = keywords(sentence)
    # Topic is a fallback context; sentence terms stay first so each scene is searched individually.
    query = " ".join(terms[:6]) if terms else topic
    found = commons_search(query, limit=8)
    if not found and topic.lower() not in query.lower():
        found = commons_search(topic, limit=8)
    return found, query

def download_for_sentence(sentence, topic, index, credits):
    found, query = search_for_sentence(sentence, topic, index)
    for rank, item in enumerate(found):
        try:
            response = requests.get(item["url"], headers={"User-Agent": UA}, timeout=30)
            response.raise_for_status()
            path = ASSETS / f"sentence_{index:03d}_candidate_{rank:02d}.jpg"
            path.write_bytes(response.content)
            with Image.open(path) as im:
                im.verify()
            item["local_path"] = str(path)
            item["matched_sentence"] = sentence
            item["search_query"] = query
            item["selection_method"] = "per-sentence Wikimedia Commons keyword search; best title overlap first"
            credits.append(item)
            return path, item
        except Exception as exc:
            print("Skipping image candidate:", item.get("title"), exc)
    return None, {"matched_sentence": sentence, "search_query": query, "selection_method": "original abstract fallback", "source": ""}

def abstract_background(index):
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line((0, y, W, y), fill=(int(4 + 9*t), int(18 + 25*t), int(38 + 45*t)))
    for j in range(13):
        x = (index*173 + j*277) % W
        y = (index*131 + j*149) % H
        r = 25 + (j*23) % 130
        d.ellipse((x-r, y-r, x+r, y+r), outline=(40, 125, 165), width=4)
    return im

def make_scene(sentence, index, total, image_path, topic, output):
    if image_path:
        with Image.open(image_path) as source:
            source = source.convert("RGB")
            scale = max(W/source.width, H/source.height)
            source = source.resize((int(source.width*scale), int(source.height*scale)), Image.Resampling.LANCZOS)
            x, y = (source.width-W)//2, (source.height-H)//2
            im = source.crop((x, y, x+W, y+H))
            im = ImageEnhance.Brightness(im).enhance(0.58)
    else:
        im = abstract_background(index)
    im = im.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0,0,0,0))
    ImageDraw.Draw(overlay).rectangle((50, 45, W-50, H-45), fill=(0,0,0,45))
    im = Image.alpha_composite(im, overlay)
    d = ImageDraw.Draw(im)
    d.text((90, 55), topic[:90].upper(), font=font(42, True), fill=(145,225,255),
           stroke_width=2, stroke_fill=(0,0,0))
    d.rounded_rectangle((60, 500, W-60, 1015), radius=38,
                        fill=(0,0,0,198), outline=(115,220,255,235), width=4)
    # Large, high-contrast captions designed for phone and desktop viewing.
    f = font(82, True)
    words = sentence.split()
    lines, line = [], ""
    for word in words:
        candidate = (line + " " + word).strip()
        if d.textbbox((0,0), candidate, font=f, stroke_width=2)[2] > W-180 and line:
            lines.append(line); line = word
        else:
            line = candidate
    if line: lines.append(line)
    lines = lines[:5]
    heights = [d.textbbox((0,0), ln, font=f, stroke_width=2)[3] for ln in lines]
    y = 760 - sum(heights)//2 - (len(lines)-1)*10
    for ln, height in zip(lines, heights):
        width = d.textbbox((0,0), ln, font=f, stroke_width=1)[2]
        d.text(((W-width)//2, y), ln, font=f, fill="white", stroke_width=3, stroke_fill="black")
        y += height + 24
    d.text((90, H-62), f"SCENE {index+1:03d}/{total:03d}  •  LONG-FORM DRAFT",
           font=font(32, True), fill=(255,255,255), stroke_width=2, stroke_fill=(0,0,0))
    im.convert("RGB").save(output, quality=92)

async def synthesize(script, voice, path):
    import edge_tts
    await edge_tts.Communicate(script, voice).save(str(path))

def srt_time(seconds):
    ms = int(seconds*1000); h = ms//3600000; ms %= 3600000
    m = ms//60000; ms %= 60000; s = ms//1000; ms %= 1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    topic = os.environ["TOPIC"].strip()
    script = os.environ["SCRIPT_TEXT"].strip()
    voice = os.environ.get("VOICE", "en-US-AriaNeural").strip()
    if not topic or not script:
        raise SystemExit("Topic and script are required.")
    OUT.mkdir(parents=True, exist_ok=True); ASSETS.mkdir(parents=True, exist_ok=True)
    parts = split_sentences(script)
    if len(parts) < 3:
        raise SystemExit("Please provide a complete long-form script split into several sentences.")
    credits, scenes, matches = [], [], []
    for i, sentence in enumerate(parts):
        image_path, match = download_for_sentence(sentence, topic, i, credits)
        matches.append({"scene": i+1, "sentence": sentence, "image_title": match.get("title", "Original abstract background"),
                        "search_query": match.get("search_query", ""), "source": match.get("source", ""),
                        "artist": match.get("artist", ""), "license": match.get("license", ""),
                        "selection_method": match.get("selection_method", "")})
        scene_path = ASSETS / f"scene_{i:03d}.jpg"
        make_scene(sentence, i, len(parts), image_path, topic, scene_path)
        scenes.append(scene_path)
    (OUT/"image_credits.json").write_text(json.dumps(credits, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT/"scene_image_matches.json").write_text(json.dumps(matches, indent=2, ensure_ascii=False), encoding="utf-8")
    narration = OUT/"narration.mp3"
    asyncio.run(synthesize(script, voice, narration))
    duration = float(subprocess.check_output(
        ["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(narration)],
        text=True).strip())
    if duration < 300 or duration > 600:
        print(f"WARNING: narration is {duration/60:.2f} minutes; requested target is 5–10 minutes. Review script length.")
    weights = [max(1, len(p.split())) for p in parts]
    durations = [duration*w/sum(weights) for w in weights]
    concat = ASSETS/"scenes.txt"
    with concat.open("w", encoding="utf-8") as f:
        for scene, seconds in zip(scenes, durations):
            f.write(f"file '{scene.resolve().as_posix()}'\nduration {seconds:.4f}\n")
        f.write(f"file '{scenes[-1].resolve().as_posix()}'\n")
    music = OUT/"ambient_bed.wav"
    run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=110:sample_rate=44100",
         "-f","lavfi","-i","sine=frequency=164.81:sample_rate=44100",
         "-filter_complex","[0:a]volume=0.025[a0];[1:a]volume=0.012[a1];[a0][a1]amix=inputs=2:duration=longest,lowpass=f=450",
         "-t",f"{duration:.3f}","-ac","2",str(music)])
    video = OUT/"youtube_long_draft.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(narration),"-i",str(music),
         "-filter_complex","[1:a]volume=1.0[voice];[2:a]volume=0.12[bed];[voice][bed]amix=inputs=2:duration=first:dropout_transition=2[aout]",
         "-map","0:v","-map","[aout]","-r","30","-vf","scale=1920:1080,format=yuv420p",
         "-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","160k","-shortest",
         "-movflags","+faststart",str(video)])
    (OUT/"script.txt").write_text(script+"\n", encoding="utf-8")
    elapsed, entries = 0, []
    for i, (sentence, seconds) in enumerate(zip(parts, durations), 1):
        entries.append(f"{i}\n{srt_time(elapsed)} --> {srt_time(elapsed+seconds)}\n{sentence}\n")
        elapsed += seconds
    (OUT/"captions.srt").write_text("\n".join(entries), encoding="utf-8")
    (OUT/"REVIEW_BEFORE_USE.txt").write_text(
        "DRAFT ONLY: this workflow never uploads, schedules, or publishes to YouTube.\n"
        "Landscape 16:9, 1920x1080. Intended narration target: 5–10 minutes; check the duration warning in logs.\n"
        "Images are searched separately for each sentence using its meaningful keywords; inspect scene_image_matches.json to review selections. Matching is keyword-based, not AI image understanding, so review every scene.\n"
        "image_credits.json lists downloaded Commons image sources, artists, and license metadata. Confirm each license and attribution requirements before reuse.\n"
        "If no suitable Commons image is found, an original abstract background is used.\n"
        "Ambient audio is synthesized, not a commercial music track. Caption timing is estimated from sentence word counts; review synchronization.\n",
        encoding="utf-8")
    print("Created review-only landscape draft:", video)
    print(f"Narration duration: {duration/60:.2f} minutes")
    print("Review scene_image_matches.json and image_credits.json before use.")
    print("No YouTube upload, scheduling, or publishing performed.")

if __name__ == "__main__":
    main()
