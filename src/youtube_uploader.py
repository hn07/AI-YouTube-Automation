import logging
from datetime import datetime, timezone
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

log = logging.getLogger("ytauto")
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def upload_and_schedule(video_path: str, title: str, description: str, tags: list[str],
                        publish_at: datetime, credentials_file="credentials/client_secret.json",
                        token_file="credentials/token.json", privacy="private"):
    cred_path = Path(credentials_file)
    if not cred_path.exists():
        raise FileNotFoundError(f"OAuth client JSON missing: {cred_path}. Follow README YouTube OAuth setup.")
    token_path = Path(token_file)
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    youtube = build("youtube", "v3", credentials=creds)
    if publish_at.tzinfo is None:
        raise ValueError("Publish time must include a timezone.")
    publish_utc = publish_at.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:30],
            "categoryId": "27",
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "publishAt": publish_utc,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media, notifySubscribers=False)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("YouTube upload progress: %d%%", int(status.progress()*100))
    return response
