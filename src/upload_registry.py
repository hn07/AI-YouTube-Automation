from pathlib import Path
import hashlib, json
from datetime import datetime
ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'output' / 'upload_registry.json'
def file_fingerprint(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()
def load_registry():
    if not REGISTRY.exists(): return []
    data = json.loads(REGISTRY.read_text(encoding='utf-8'))
    if not isinstance(data, list): raise RuntimeError('Upload registry format is invalid')
    return data
def find_duplicate(path):
    digest = file_fingerprint(path)
    return next((item for item in load_registry() if item.get('sha256') == digest), None)
def record_upload(path, video_id, title, scheduled_time):
    items = load_registry()
    digest = file_fingerprint(path)
    if any(item.get('sha256') == digest for item in items): raise RuntimeError('MP4 already exists in upload registry')
    items.append({'sha256': digest, 'video_id': video_id, 'title': title, 'scheduled_time': scheduled_time, 'uploaded_at': datetime.now().astimezone().isoformat(timespec='seconds'), 'video_path': str(Path(path).resolve())})
    REGISTRY.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding='utf-8')
