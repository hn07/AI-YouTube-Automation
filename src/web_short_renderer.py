#!/usr/bin/env python3
"""Render a review-only vertical Short. Never uploads or publishes."""
import asyncio, json, os, re, subprocess
from pathlib import Path
from urllib.parse import quote
import requests
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

ROOT=Path("render-work"); ASSETS=ROOT/"assets"; OUT=Path("rendered-draft")
W,H=1080,1920
UA="AI-YouTube-Automation/1.0 (review-only renderer)"

def run(cmd):
    subprocess.run(cmd, check=True)

def font(size,bold=False):
    p="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(p,size) if Path(p).exists() else ImageFont.load_default()

def split_sentences(text):
    items=[x.strip() for x in re.split(r"(?<=[.!?])\s+",text.strip()) if x.strip()]
    return items or [text.strip()]

def commons_search(topic):
    params={"action":"query","format":"json","generator":"search","gsrsearch":f"filetype:bitmap {topic}","gsrnamespace":6,"gsrlimit":8,"prop":"imageinfo","iiprop":"url|extmetadata","iiurlwidth":1200}
    try:
        data=requests.get("https://commons.wikimedia.org/w/api.php",params=params,headers={"User-Agent":UA},timeout=25).json()
    except Exception as exc:
        print("Wikimedia Commons search unavailable; using original abstract backgrounds:",exc); return []
    results=[]
    for page in ((data.get("query") or {}).get("pages") or {}).values():
        info=(page.get("imageinfo") or [{}])[0]; url=info.get("thumburl") or info.get("url")
        if not url: continue
        meta=info.get("extmetadata") or {}
        def val(k):
            raw=(meta.get(k) or {}).get("value","")
            return re.sub(r"<[^>]*>","",raw).strip()
        title=page.get("title","Untitled")
        results.append({"title":title,"url":url,"artist":val("Artist") or "Not listed","license":val("LicenseShortName") or "Check source","credit":val("Credit"),"source":"https://commons.wikimedia.org/wiki/"+quote(title.replace(" ","_"))})
    return results

def download_backgrounds(topic):
    ASSETS.mkdir(parents=True,exist_ok=True); credits=[]; paths=[]
    for i,item in enumerate(commons_search(topic)):
        try:
            r=requests.get(item["url"],headers={"User-Agent":UA},timeout=30); r.raise_for_status()
            p=ASSETS/f"commons_{i:02d}.jpg"; p.write_bytes(r.content)
            with Image.open(p) as im: im.verify()
            item["local_path"]=str(p); paths.append(p); credits.append(item)
        except Exception as exc: print("Skipping image:",item.get("title"),exc)
    (OUT/"image_credits.json").write_text(json.dumps(credits,indent=2,ensure_ascii=False),encoding="utf-8")
    return paths

def background(index,topic):
    im=Image.new("RGB",(W,H)); d=ImageDraw.Draw(im)
    for y in range(H):
        t=y/H; d.line((0,y,W,y),fill=(int(5+8*t),int(18+25*t),int(40+42*t)))
    for j in range(9):
        x=(index*173+j*211)%W; y=(index*251+j*307)%H; r=30+(j*17)%100
        d.ellipse((x-r,y-r,x+r,y+r),outline=(40,125,165),width=4)
    return im

def make_scene(sentence,index,total,photos,topic,path):
    if photos:
        with Image.open(photos[index%len(photos)]) as src:
            src=src.convert("RGB"); scale=max(W/src.width,H/src.height)
            src=src.resize((int(src.width*scale),int(src.height*scale)),Image.Resampling.LANCZOS)
            x=(src.width-W)//2; y=(src.height-H)//2
            im=src.crop((x,y,x+W,y+H)); im=ImageEnhance.Brightness(im).enhance(.48)
    else: im=background(index,topic)
    im=im.convert("RGBA")
    overlay=Image.new("RGBA",(W,H),(0,0,0,0)); od=ImageDraw.Draw(overlay)
    od.rectangle((45,150,W-45,H-150),fill=(0,0,0,65))
    im=Image.alpha_composite(im,overlay); d=ImageDraw.Draw(im)
    d.text((72,90),topic[:50].upper(),font=font(42,True),fill=(125,225,255),stroke_width=2,stroke_fill=(0,0,0))
    d.rounded_rectangle((55,590,W-55,1350),radius=32,fill=(0,0,0,178),outline=(95,205,245,200),width=3)
    lines=[]; line=""
    for word in sentence.split():
        candidate=(line+" "+word).strip()
        if len(candidate)>24 and line: lines.append(line); line=word
        else: line=candidate
    if line: lines.append(line)
    lines=lines[:8]; y=970-len(lines)*42
    for ln in lines:
        f=font(58,True); box=d.textbbox((0,0),ln,font=f,stroke_width=2)
        d.text(((W-(box[2]-box[0]))//2,y),ln,font=f,fill="white",stroke_width=2,stroke_fill="black"); y+=85
    d.text((72,H-115),f"SCENE {index+1:02d}/{total:02d}  •  DRAFT",font=font(30),fill=(230,245,250))
    im.convert("RGB").save(path,quality=92)

async def synthesize(script,voice,path):
    import edge_tts
    await edge_tts.Communicate(script,voice).save(str(path))

def srt_time(sec):
    ms=int(sec*1000); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; ms%=1000
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def main():
    topic=os.environ["TOPIC"].strip(); script=os.environ["SCRIPT_TEXT"].strip()
    voice=os.environ.get("VOICE","en-US-AriaNeural").strip()
    if not topic or not script: raise SystemExit("Topic and script are required.")
    OUT.mkdir(parents=True,exist_ok=True); ASSETS.mkdir(parents=True,exist_ok=True)
    parts=split_sentences(script); photos=download_backgrounds(topic); scenes=[]
    for i,part in enumerate(parts):
        p=ASSETS/f"scene_{i:03d}.jpg"; make_scene(part,i,len(parts),photos,topic,p); scenes.append(p)
    narration=OUT/"narration.mp3"; asyncio.run(synthesize(script,voice,narration))
    duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(narration)],text=True).strip())
    weights=[max(1,len(p.split())) for p in parts]; durations=[duration*w/sum(weights) for w in weights]
    concat=ASSETS/"scenes.txt"
    with concat.open("w",encoding="utf-8") as f:
        for p,dur in zip(scenes,durations): f.write(f"file '{p.resolve().as_posix()}'\nduration {dur:.4f}\n")
        f.write(f"file '{scenes[-1].resolve().as_posix()}'\n")
    music=OUT/"ambient_bed.wav"
    run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=110:sample_rate=44100","-f","lavfi","-i","sine=frequency=164.81:sample_rate=44100","-filter_complex","[0:a]volume=0.035[a0];[1:a]volume=0.018[a1];[a0][a1]amix=inputs=2:duration=longest,lowpass=f=450","-t",f"{duration:.3f}","-ac","2",str(music)])
    video=OUT/"youtube_short_draft.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(narration),"-i",str(music),"-filter_complex","[1:a]volume=1.0[voice];[2:a]volume=0.18[bed];[voice][bed]amix=inputs=2:duration=first:dropout_transition=2[aout]","-map","0:v","-map","[aout]","-r","30","-vf","scale=1080:1920,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","23","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(video)])
    (OUT/"script.txt").write_text(script+"\n",encoding="utf-8")
    elapsed=0; entries=[]
    for i,(part,dur) in enumerate(zip(parts,durations),1):
        entries.append(f"{i}\n{srt_time(elapsed)} --> {srt_time(elapsed+dur)}\n{part}\n"); elapsed+=dur
    (OUT/"captions.srt").write_text("\n".join(entries),encoding="utf-8")
    (OUT/"REVIEW_BEFORE_USE.txt").write_text(
        "DRAFT ONLY: this workflow never uploads, schedules, or publishes to YouTube.\n"
        "Review script accuracy, voice pronunciation, visual relevance, captions, and audio mix.\n"
        "Wikimedia Commons image sources, artists, and licenses are listed in image_credits.json. Confirm license/attribution requirements before reuse.\n"
        "If no Commons images download, original abstract backgrounds are generated instead.\n"
        "Ambient sound is synthesized; it is not a commercial music track.\n",encoding="utf-8")
    print("Created review-only video:",video)
    print("No YouTube upload, scheduling, or publishing performed.")

if __name__=="__main__": main()
