from __future__ import annotations
import os, re, subprocess, sys, zipfile, shutil
from datetime import datetime
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "local-output"
OUTPUT_ROOT.mkdir(exist_ok=True)
VOICES = ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"]
st.set_page_config(page_title="Nhâm YouTube Studio", page_icon="🎬", layout="wide")
st.title("🎬 Nhâm YouTube Studio")
st.caption("Windows 11 • Nhập chủ đề → tạo kịch bản → dựng video nháp")
st.info("Chỉ tạo tệp trên máy. Ứng dụng không có chức năng upload, lên lịch hoặc đăng YouTube.")
with st.sidebar:
    st.header("Cài đặt")
    kind = st.radio("Loại video", ["Shorts dọc 9:16", "Video dài ngang 16:9"])
    voice = st.selectbox("Giọng đọc tiếng Anh", VOICES)
    api_key = st.text_input("OpenRouter API key (không bắt buộc)", type="password",
        help="Dùng thử model miễn phí nếu tài khoản được cấp quyền. Khóa chỉ dùng trong phiên này, không lưu vào tệp.")
    st.caption("Không có API key: dùng kịch bản mẫu miễn phí, không phải mô hình AI.")
topic = st.text_input("Chủ đề video", placeholder="Ví dụ: Strange Creatures of the Deep Ocean")
create = st.button("✨ Tạo kịch bản và dựng video", type="primary", use_container_width=True)

def fallback_script(topic: str, long_form: bool) -> str:
    t = re.sub(r"\s+", " ", topic).strip()
    if not long_form:
        return (f"Have you ever wondered about {t}? The most interesting part is often not the first thing people notice. "
        f"To understand {t}, start by asking what is actually known and what still needs evidence. "
        f"Look for reliable explanations, compare more than one source, and be careful with claims that sound unbelievable. "
        f"Small details can completely change how we understand a subject. When you explore {t}, keep an open mind, "
        "but do not confuse a surprising story with a proven fact. The next time this topic comes up, ask one simple "
        "question: what evidence supports the claim? That habit makes learning more useful and helps separate facts "
        "from speculation. Follow for more curious topics explained clearly.")
    sections = [
    ("Opening", f"What makes {t} worth exploring? Some subjects seem familiar at first, yet a closer look reveals questions that are harder to answer. In this video, we will explore the main ideas behind {t}, separate common assumptions from information that can be checked, and consider why the subject attracts attention."),
    ("Background", f"To understand {t}, it helps to begin with the background. Every subject has a context: how people first became interested in it, which observations shaped the discussion, and how explanations changed over time. Rather than accepting the most dramatic version of a story, look for original sources and understand what they actually say."),
    ("What people miss", f"One detail people overlook when discussing {t} is the difference between an observation and an interpretation. An observation describes what was recorded or measured. An interpretation explains what someone thinks that observation means. These can be related, but they are not identical. Keeping them separate makes it easier to evaluate claims fairly."),
    ("Evidence", f"A careful investigation of {t} starts with evidence. Reliable explanations make their sources clear, describe uncertainty, and allow other people to check the reasoning. If sources disagree, compare their dates, methods, expertise, and references. A confident tone alone is not proof, and a popular claim can still be incomplete or mistaken."),
    ("Why it matters", f"The reason {t} remains interesting is that it invites people to ask better questions. Sometimes new information changes an established explanation. In other cases, the evidence supports a more ordinary answer than an exciting headline suggests. Either way, checking claims can be more valuable than rushing toward a conclusion."),
    ("Misunderstandings", f"When learning about {t}, watch for exaggerated summaries, missing context, and statements that treat a possibility as certainty. Ask what is directly supported, what is inferred, and what remains unknown. Seek more than one trustworthy source and follow citations to their origin instead of relying only on a social media post."),
    ("Explore it yourself", f"You can investigate {t} by writing down the main question, finding a credible introductory source, and checking the evidence it cites. Compare that account with another independent source. Note disagreements and whether they come from different evidence or different interpretations. This approach works for science, history, technology, and everyday questions."),
    ("Conclusion", f"So, what should we take away from {t}? Stay curious, be willing to revise your view, and make room for uncertainty when evidence is incomplete. Interesting topics deserve more than a dramatic headline; they deserve careful questions and clear explanations. Thanks for watching. Keep exploring, check the sources, and look for the evidence behind the story.")
    ]
    return "\n\n".join(f"{h}. {body}" for h, body in sections)

def generate_ai_script(topic: str, long_form: bool, key: str) -> str:
    import requests
    target = "700–1000" if long_form else "110–150"
    prompt = ("Write an engaging English YouTube narration about this topic. Target " + target +
      " words. Use a strong opening, clear transitions, and a satisfying ending. Return narration only, without markdown or production notes. "
      "Avoid unsupported precise statistics, invented citations, and presenting uncertainty as fact. Topic: " + topic)
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
      "HTTP-Referer": "http://localhost", "X-Title": "Nham YouTube Studio Local"},
      json={"model":"meta-llama/llama-3.3-70b-instruct:free",
      "messages":[{"role":"user","content":prompt}],"temperature":0.7}, timeout=90)
    response.raise_for_status()
    script = response.json()["choices"][0]["message"]["content"].strip()
    if len(script.split()) < (450 if long_form else 60):
        raise ValueError("AI trả về kịch bản quá ngắn.")
    return script

if create:
    if not topic.strip():
        st.error("Vui lòng nhập chủ đề.")
        st.stop()
    long_form = kind.startswith("Video dài")
    ffmpeg = shutil.which("ffmpeg") or (str(ROOT/"tools"/"ffmpeg"/"bin"/"ffmpeg.exe") if (ROOT/"tools"/"ffmpeg"/"bin"/"ffmpeg.exe").exists() else None)
    ffprobe = shutil.which("ffprobe") or (str(Path(ffmpeg).with_name("ffprobe.exe")) if ffmpeg and Path(ffmpeg).with_name("ffprobe.exe").exists() else None)
    if not ffmpeg or not ffprobe:
        st.error("Chưa tìm thấy FFmpeg/FFprobe. Xem LOCAL_STUDIO_GUIDE.md để cài đặt.")
        st.stop()
    slug = re.sub(r"[^A-Za-z0-9_-]+", "_", topic).strip("_")[:40] or "video"
    job = OUTPUT_ROOT/(datetime.now().strftime("%Y%m%d_%H%M%S")+"_"+slug)
    job.mkdir(parents=True, exist_ok=True)
    status = st.status("Đang tạo kịch bản…", expanded=True)
    try:
        source = "Bộ tạo kịch bản mẫu miễn phí (không phải AI)"
        if api_key.strip():
            try:
                script = generate_ai_script(topic.strip(), long_form, api_key.strip())
                source = "OpenRouter model miễn phí nếu còn khả dụng"
            except Exception as exc:
                st.warning(f"Không gọi được AI miễn phí: {exc}. Đã chuyển sang kịch bản mẫu.")
                script = fallback_script(topic.strip(), long_form)
        else:
            script = fallback_script(topic.strip(), long_form)
        (job/"script.txt").write_text(script+"\n", encoding="utf-8")
        (job/"topic.txt").write_text(topic.strip()+"\n", encoding="utf-8")
        (job/"SCRIPT_SOURCE.txt").write_text(source+"\n", encoding="utf-8")
        status.write(f"Kịch bản: {len(script.split())} từ. Nguồn: {source}")
        status.write("Đang tìm ảnh và dựng video. Quá trình này cần Internet.")
        renderer = ROOT/"src"/("web_long_renderer.py" if long_form else "web_short_renderer.py")
        env = os.environ.copy()
        env.update({"TOPIC":topic.strip(), "SCRIPT_TEXT":script, "VOICE":voice, "PYTHONIOENCODING":"utf-8"})
        result = subprocess.run([sys.executable,str(renderer)], cwd=str(job), env=env,
          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=2400)
        (job/"render.log").write_text((result.stdout or "")+"\n--- STDERR ---\n"+(result.stderr or ""), encoding="utf-8")
        if result.returncode:
            raise RuntimeError("Dựng video thất bại. Mở render.log trong thư mục công việc để xem lỗi.")
        render_dir = job/("rendered-long-draft" if long_form else "rendered-draft")
        mp4 = render_dir/("youtube_long_draft.mp4" if long_form else "youtube_short_draft.mp4")
        if not mp4.exists():
            raise FileNotFoundError("Không tìm thấy MP4 đầu ra: "+str(mp4))
        package = job/"video_package.zip"
        with zipfile.ZipFile(package,"w",zipfile.ZIP_DEFLATED) as z:
            for p in render_dir.rglob("*"):
                if p.is_file(): z.write(p,p.relative_to(job))
            for name in ["script.txt","topic.txt","SCRIPT_SOURCE.txt","render.log"]:
                p=job/name
                if p.exists(): z.write(p,p.relative_to(job))
        status.update(label="Đã tạo video nháp",state="complete",expanded=False)
        st.success("Hoàn tất: "+mp4.name)
        st.video(str(mp4))
        st.download_button("⬇️ Tải MP4",mp4.read_bytes(),file_name=mp4.name,mime="video/mp4",use_container_width=True)
        st.download_button("📦 Tải gói video ZIP",package.read_bytes(),file_name=package.name,mime="application/zip",use_container_width=True)
        st.caption("Đã lưu tại: "+str(job))
        st.warning("Kiểm tra kịch bản, hình ảnh, giấy phép và phụ đề trước khi sử dụng. Không có nội dung nào được tải lên YouTube.")
    except subprocess.TimeoutExpired:
        status.update(label="Quá thời gian dựng video",state="error")
        st.error("Quá 40 phút. Kiểm tra mạng và render.log.")
    except Exception as exc:
        status.update(label="Tạo video chưa thành công",state="error")
        st.error(str(exc))
        st.caption("Thư mục công việc: "+str(job))
else:
    st.subheader("Cách dùng")
    st.markdown("1. Nhập chủ đề.\\n2. Chọn Shorts hoặc video dài ở thanh bên.\\n3. Chọn giọng đọc.\\n4. (Không bắt buộc) nhập API key từ dịch vụ có model miễn phí.\\n5. Bấm **Tạo kịch bản và dựng video** rồi chờ hoàn tất.\\n6. Tải MP4 hoặc ZIP về máy.")
    st.warning("Không có API key thì ứng dụng dùng kịch bản mẫu, không phải AI và nội dung có thể chung chung. Giọng đọc và tìm ảnh cần Internet.")
st.divider()
st.caption("Local Studio V1 • Tạo video nháp • Không upload / schedule / publish YouTube")
