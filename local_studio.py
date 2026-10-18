from __future__ import annotations
import os, re, subprocess, sys, zipfile, shutil, json
from datetime import datetime, date, time, timedelta, timezone
from pathlib import Path
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = ROOT / "local-output"
OUTPUT_ROOT.mkdir(exist_ok=True)
VOICES = ["en-US-AriaNeural", "en-US-GuyNeural", "en-US-JennyNeural"]
st.set_page_config(page_title="Nhâm YouTube Studio", page_icon="🎬", layout="wide")
st.title("🎬 Nhâm YouTube Studio")
st.caption("Windows 11 • Nhập chủ đề → tạo kịch bản → dựng video nháp")
st.info("Tạo video nháp trước. Chỉ tải lên và đặt lịch YouTube khi bạn chủ động xác nhận trong mục Lịch đăng.")
with st.sidebar:
    st.header("Cài đặt")
    kind = st.radio("Loại video", ["Shorts dọc 9:16", "Video dài ngang 16:9"])
    voice = st.selectbox("Giọng đọc tiếng Anh", VOICES)
    api_key = st.text_input("OpenRouter API key (không bắt buộc)", type="password",
        help="Dán toàn bộ khóa riêng tư bắt đầu bằng sk-or-v1-. Không chia sẻ khóa này.")
    ai_model = st.selectbox("Mô hình tạo kịch bản", [
        "openrouter/free",
        "nvidia/nemotron-3-ultra-253b-a22b:free",
        "google/gemma-3-27b-it:free",
    ], help="Ưu tiên openrouter/free để tự chọn một model miễn phí đang hoạt động. Danh sách miễn phí có thể thay đổi.")
    if st.button("🔌 Kiểm tra API key và model", use_container_width=True):
        if not api_key.strip():
            st.error("Hãy nhập API key trước.")
        else:
            try:
                import requests as _requests
                _res = _requests.post("https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization":"Bearer "+api_key.strip(),"Content-Type":"application/json",
                             "HTTP-Referer":"http://localhost","X-Title":"Nham YouTube Studio Local"},
                    json={"model":ai_model,"messages":[{"role":"user","content":"Reply with exactly: API OK"}],"max_tokens":20},
                    timeout=45)
                if _res.ok:
                    st.success("API hoạt động: "+str(_res.json().get("choices",[{}])[0].get("message",{}).get("content","OK")))
                else:
                    st.error(f"OpenRouter HTTP {_res.status_code}: "+str((_res.text or "")[:1000]))
            except Exception as _exc:
                st.error("Không kết nối được OpenRouter: "+str(_exc))
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

def generate_ai_script(topic: str, long_form: bool, key: str, model: str) -> str:
    import requests
    target = "700–1000" if long_form else "110–150"
    prompt = ("Write an engaging English YouTube narration about this topic. Target " + target +
      " words. Use a strong opening, clear transitions, and a satisfying ending. Return narration only, without markdown or production notes. "
      "Avoid unsupported precise statistics, invented citations, and presenting uncertainty as fact. Topic: " + topic)
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
      headers={"Authorization": "Bearer " + key, "Content-Type": "application/json",
      "HTTP-Referer": "http://localhost", "X-Title": "Nham YouTube Studio Local"},
      json={"model":model,
      "messages":[{"role":"user","content":prompt}],"temperature":0.7}, timeout=90)
    if not response.ok:
        detail = response.text[:1200]
        raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {detail}")

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
                script = generate_ai_script(topic.strip(), long_form, api_key.strip(), ai_model)
                source = "OpenRouter: "+ai_model
            except Exception as exc:
                st.error(f"Không gọi được AI: {exc}")
                st.stop()
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
    st.warning("Không có API key thì ứng dụng dùng kịch bản mẫu, không phải AI. Nếu API lỗi, app sẽ hiển thị nguyên nhân và dừng thay vì âm thầm tạo kịch bản mẫu.")
st.divider()
st.header("🗓️ Lịch đăng YouTube")
st.markdown("Chọn video đã dựng, nhập thông tin và thời điểm đăng. Ứng dụng **không tự đăng nền**: video chỉ được tải lên và lên lịch sau khi bạn đánh dấu xác nhận và bấm nút bên dưới.")
client_file = ROOT / "client_secret.json"
with st.expander("⚙️ Thiết lập Google OAuth (làm một lần)", expanded=not client_file.exists()):
    st.markdown("1. Mở Google Cloud Console, tạo/chọn project và bật **YouTube Data API v3**.\n2. Cấu hình OAuth consent screen; nếu ở chế độ Testing, thêm tài khoản Google vào Test users.\n3. Tạo OAuth Client ID loại **Desktop app** và tải JSON.\n4. Chọn tệp JSON ở dưới rồi lưu cấu hình cục bộ. Không tải tệp này lên GitHub.")
    oauth_upload = st.file_uploader("Chọn OAuth Client JSON đã tải từ Google Cloud", type=["json"], key="oauth_client_upload")
    if oauth_upload is not None:
        try:
            parsed = json.loads(oauth_upload.getvalue().decode("utf-8"))
            if not isinstance(parsed, dict) or not (parsed.get("installed") or parsed.get("web")):
                raise ValueError("JSON không giống OAuth client của Google (thiếu installed/web).")
            if st.button("💾 Lưu cấu hình OAuth trên máy này", key="save_oauth_config"):
                client_file.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
                st.success("Đã lưu client_secret.json cục bộ. Tải lại trang nếu trạng thái chưa đổi.")
        except Exception as exc:
            st.error("Tệp JSON không hợp lệ: "+str(exc))
    if client_file.exists():
        st.success("Đã tìm thấy client_secret.json.")
    else:
        st.info("Chưa có OAuth JSON. Chức năng đăng lịch chỉ hoạt động sau khi bạn thêm tệp này.")
video_candidates = sorted(OUTPUT_ROOT.glob("**/*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
if not video_candidates:
    st.caption("Chưa có MP4 nào. Hãy tạo video trước.")
else:
    selected_video = st.selectbox("Video cần lên lịch", video_candidates, format_func=lambda p: f"{p.parent.parent.name} — {p.name}")
    with st.form("youtube_schedule_form"):
        yt_title = st.text_input("Tiêu đề YouTube", value=selected_video.parent.parent.name.replace("_", " ")[:100], max_chars=100)
        yt_description = st.text_area("Mô tả video", value="Created with Nham YouTube Studio.", height=100, max_chars=5000)
        col_date, col_time = st.columns(2)
        with col_date:
            schedule_date = st.date_input("Ngày đăng", value=date.today() + timedelta(days=1), min_value=date.today())
        with col_time:
            schedule_time = st.time_input("Giờ đăng (giờ Việt Nam)", value=time(19, 0), step=900)
        audience = st.selectbox("Đối tượng", ["Không dành riêng cho trẻ em", "Dành cho trẻ em"])
        confirmed = st.checkbox("Tôi đã xem lại video, có quyền sử dụng hình/âm thanh và xác nhận tải video lên YouTube ở chế độ riêng tư để lên lịch.")
        submit_schedule = st.form_submit_button("🔐 Đăng nhập Google và tải lên / lên lịch", type="primary", use_container_width=True)
    if submit_schedule:
        if not client_file.exists():
            st.error("Thiếu client_secret.json. Hãy thiết lập OAuth trong Google Cloud Console trước.")
        elif not yt_title.strip():
            st.error("Vui lòng nhập tiêu đề video.")
        elif not confirmed:
            st.error("Bạn cần đánh dấu xác nhận trước khi tải video lên.")
        else:
            local_dt = datetime.combine(schedule_date, schedule_time).replace(tzinfo=timezone(timedelta(hours=7)))
            if local_dt <= datetime.now(timezone(timedelta(hours=7))) + timedelta(minutes=2):
                st.error("Chọn thời điểm trong tương lai ít nhất 2 phút.")
            else:
                try:
                    from google.oauth2.credentials import Credentials
                    from google_auth_oauthlib.flow import InstalledAppFlow
                    from google.auth.transport.requests import Request
                    from googleapiclient.discovery import build
                    from googleapiclient.http import MediaFileUpload
                    token_file = ROOT / "youtube_token.json"
                    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
                    creds = None
                    if token_file.exists():
                        creds = Credentials.from_authorized_user_file(str(token_file), scopes)
                    if not creds or not creds.valid:
                        if creds and creds.expired and creds.refresh_token:
                            creds.refresh(Request())
                        else:
                            flow = InstalledAppFlow.from_client_secrets_file(str(client_file), scopes)
                            creds = flow.run_local_server(port=0, prompt="consent")
                        token_file.write_text(creds.to_json(), encoding="utf-8")
                    youtube = build("youtube", "v3", credentials=creds)
                    publish_at = local_dt.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
                    body = {"snippet": {"title": yt_title.strip(), "description": yt_description.strip(), "categoryId": "22"},
                            "status": {"privacyStatus": "private", "publishAt": publish_at,
                                       "selfDeclaredMadeForKids": audience == "Dành cho trẻ em"}}
                    media = MediaFileUpload(str(selected_video), mimetype="video/*", resumable=True)
                    with st.spinner("Đang tải video lên YouTube và thiết lập lịch đăng…"):
                        response = youtube.videos().insert(part="snippet,status", body=body, media_body=media).execute()
                    st.success("Đã tải lên và đặt lịch thành công.")
                    st.write("YouTube video ID:", response.get("id", ""))
                    st.write("Thời điểm đăng theo giờ Việt Nam:", local_dt.strftime("%d/%m/%Y %H:%M"))
                    st.markdown(f"[Mở video trong YouTube Studio](https://studio.youtube.com/video/{response.get('id','')}/edit)")
                except Exception as exc:
                    st.error(f"Không thể lên lịch YouTube: {exc}")
                    st.caption("Kiểm tra quyền YouTube Data API v3, OAuth Client kiểu Desktop app, hạn mức API và trạng thái kênh.")

st.caption("Local Studio V1.1 • Caption lớn, hình theo từng cảnh • Chỉ upload/lên lịch khi bạn bấm xác nhận")
