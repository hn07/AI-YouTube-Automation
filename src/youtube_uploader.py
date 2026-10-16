import logging
from datetime import datetime, timezone
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

log = logging.getLogger("ytauto")
# force-ssl supports upload and reading back the video's status for schedule verification.
SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
]


def _load_credentials(cred_path: Path, token_path: Path):
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    required = set(SCOPES)
    granted = set(getattr(creds, "scopes", None) or []) if creds else set()
    missing_scope = bool(creds) and not required.issubset(granted)

    if not creds or missing_scope:
        # One-time interactive consent is required when the old token lacks read-back scope.
        flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
        creds = flow.run_local_server(port=0)
    elif creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(str(cred_path), SCOPES)
        creds = flow.run_local_server(port=0)

    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json(), encoding="utf-8")
    return creds


def upload_and_schedule(video_path: str, title: str, description: str, tags: list[str],
                        publish_at: datetime, credentials_file="credentials/client_secret.json",
                        token_file="credentials/token.json", privacy="private"):
    cred_path = Path(credentials_file)
    if not cred_path.exists():
        raise FileNotFoundError(f"OAuth client JSON missing: {cred_path}. Follow README YouTube OAuth setup.")
    token_path = Path(token_file)
    creds = _load_credentials(cred_path, token_path)
    youtube = build("youtube", "v3", credentials=creds)

    if publish_at.tzinfo is None:
        raise ValueError("Publish time must include a timezone.")
    if publish_at <= datetime.now(publish_at.tzinfo):
        raise ValueError("Publish time must be in the future.")

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
            "privacyStatus": "private",
            "publishAt": publish_utc,
            "selfDeclaredMadeForKids": False,
        },
    }
    media = MediaFileUpload(video_path, mimetype="video/mp4", chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status", body=body, media_body=media, notifySubscribers=False
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info("YouTube upload progress: %d%%", int(status.progress() * 100))

    # Do not re-upload if verification fails: the video may already exist on YouTube.
    video_id = response.get("id")
    response_status = response.get("status", {}) or {}
    verified_status = response_status
    verification_error = ""
    if video_id:
        try:
            check = youtube.videos().list(part="status", id=video_id).execute()
            items = check.get("items", [])
            if items:
                verified_status = items[0].get("status", {}) or {}
            else:
                verification_error = "YouTube status query returned no video item."
        except Exception as exc:
            verification_error = f"Upload may have succeeded, but status read-back failed: {exc}"
            log.exception("Schedule status verification failed for video_id=%s", video_id)

    actual_publish_at = verified_status.get("publishAt")
    actual_privacy = verified_status.get("privacyStatus")
    publish_time_matches = False
    if actual_publish_at:
        try:
            actual_dt = datetime.fromisoformat(actual_publish_at.replace("Z", "+00:00"))
            requested_dt = datetime.fromisoformat(publish_utc.replace("Z", "+00:00"))
            publish_time_matches = abs((actual_dt - requested_dt).total_seconds()) <= 60
        except (TypeError, ValueError):
            publish_time_matches = False
    verified = bool(actual_publish_at and actual_privacy == "private" and publish_time_matches)
    if not actual_publish_at and not verification_error:
        verification_error = "YouTube did not return publishAt; check YouTube Studio manually."
    elif actual_publish_at and not publish_time_matches:
        verification_error = (
            f"YouTube publishAt does not match requested time: requested={publish_utc}, "
            f"actual={actual_publish_at}. Check YouTube Studio manually."
        )
    elif actual_publish_at and actual_privacy != "private":
        verification_error = f"Expected privacyStatus=private but API returned {actual_privacy!r}."
    response["status"] = verified_status
    response["schedule_verified"] = verified
    response["verification_error"] = verification_error
    response["requested_publish_at"] = publish_utc
    response["schedule_verified_publish_at"] = actual_publish_at
    response["schedule_verified_privacy"] = actual_privacy
    if not verified:
        log.warning("Schedule not confirmed video_id=%s publishAt=%s privacy=%s error=%s",
                    video_id, actual_publish_at, actual_privacy, verification_error)
    return response
