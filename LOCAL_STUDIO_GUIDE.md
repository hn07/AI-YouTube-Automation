# Nham YouTube Studio Local V1 (Windows 11)

## Tính năng
- Giao diện tiếng Việt chạy trên máy tại http://localhost:8501.
- Chỉ cần nhập chủ đề; chọn Shorts 9:16 hoặc video dài 16:9 và giọng đọc.
- Có thể nhập API key OpenRouter để thử model miễn phí tạo kịch bản theo chủ đề. Khóa chỉ dùng trong phiên giao diện, không được ghi vào tệp.
- Nếu không có API key hoặc model miễn phí không hoạt động, app dùng kịch bản mẫu dự phòng. Đây không phải mô hình AI và có thể chung chung.
- Dùng edge-tts để tạo giọng đọc, Wikimedia Commons để tìm ảnh và FFmpeg để kết xuất MP4.
- Lưu kết quả trong local-output. Có nút tải MP4 và ZIP.
- Caption lớn, tương phản cao hơn; tìm ảnh theo từng câu/cảnh và xuất scene_image_matches.json để kiểm tra.
- Có mục lên lịch YouTube có xác nhận: chỉ tải video lên khi người dùng đánh dấu đồng ý và bấm nút; không tự đăng nền.
- OAuth token được lưu cục bộ trong youtube_token.json; không chia sẻ tệp này.

## Cài đặt lần đầu
1. Cài Python 3.12 (khuyên dùng) hoặc 3.11 tại https://www.python.org/downloads/. Chọn Add Python to PATH.
2. Cài FFmpeg từ https://ffmpeg.org/download.html. Đảm bảo cả ffmpeg.exe và ffprobe.exe có trong PATH. Có thể đặt hai tệp vào tools/ffmpeg/bin/.
3. Tải ZIP của repository từ GitHub, giải nén vào thư mục mới, ví dụ D:\MyWorkSpace\AI-YouTube-Automation. Không giải nén đè lên một dự án khác.
4. Bấm đúp INSTALL_LOCAL.bat và chờ cài đặt.
5. Bấm đúp TEST_LOCAL.bat. Nếu kiểm tra đạt, bấm đúp START_LOCAL.bat.
6. Trình duyệt mở tại http://localhost:8501. Giữ cửa sổ console mở trong khi sử dụng.

## Tạo video
1. Nhập chủ đề.
2. Chọn Shorts hoặc video dài trong thanh bên.
3. Chọn giọng đọc.
4. Tùy chọn: nhập API key từ dịch vụ có model miễn phí để tạo kịch bản sát chủ đề hơn. Quyền truy cập miễn phí và model khả dụng có thể thay đổi, không được đảm bảo.
5. Bấm Tạo kịch bản và dựng video, chờ xử lý rồi tải MP4 hoặc ZIP.
6. Kết quả cũng được lưu trong local-output/<job>/.

## Lưu ý
- Nếu không có API key, kịch bản dự phòng không phải AI, có thể lặp ý hoặc thiếu thông tin chuyên biệt. Hãy kiểm tra mọi tuyên bố thực tế.
- Internet cần thiết cho giọng đọc và tìm/tải ảnh. Nếu không tải được ảnh, renderer có thể tạo nền đồ họa trừu tượng.
- Việc ghép ảnh dựa trên từ khóa, không phải hiểu ảnh bằng AI. Kiểm tra nguồn, giấy phép và yêu cầu ghi công trong image_credits.json.
- Video dài hướng tới 5–10 phút nhưng có thể cần chỉnh kịch bản nếu giọng đọc ngoài thời lượng đó.
- Dùng Python 3.11/3.12; Python 3.14 chưa được kiểm thử.
- Công cụ chỉ tạo video nháp. Không tự tải lên hoặc đăng YouTube.

## Cài đặt chức năng lên lịch YouTube
1. Trong Google Cloud Console, tạo project và bật **YouTube Data API v3**.
2. Cấu hình OAuth consent screen; thêm tài khoản Google của bạn vào danh sách Test users nếu ứng dụng đang ở chế độ Testing.
3. Tạo OAuth Client ID loại **Desktop app**, tải JSON và đổi tên thành `client_secret.json`; đặt cạnh `local_studio.py`. Không commit hoặc chia sẻ tệp này.
4. Chạy lại `INSTALL_LOCAL.bat` để cài các thư viện Google API.
5. Trong app, chọn MP4, điền tiêu đề/mô tả, ngày giờ Việt Nam, đối tượng video; đọc kỹ xác nhận rồi bấm **Đăng nhập Google và tải lên / lên lịch**.
6. Trình duyệt mở đăng nhập Google. Video được tải lên ở chế độ riêng tư với thời điểm `publishAt`; hãy kiểm tra lại trong YouTube Studio. Lần đầu có thể cần chấp thuận quyền upload.

**Lưu ý:** Lịch đăng chỉ thực hiện khi bạn bấm nút và xác nhận. Chức năng cần Internet, quyền OAuth và quota YouTube API. Không thể bảo đảm lịch được chấp nhận nếu Google chưa xác minh/cấp quyền API. Giữ riêng `client_secret.json` và `youtube_token.json`; không đưa chúng lên GitHub.
