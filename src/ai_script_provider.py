import json
import os
import re
import urllib.request


def generate(topic: str, style: str = "curiosity") -> str | None:
    """Return an AI-written script when configured; otherwise return None."""
    base = os.getenv("AI_API_BASE_URL", "").strip().rstrip("/")
    key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "").strip()
    if not (base and key and model):
        return None
    endpoint = base if base.endswith("/chat/completions") else base + "/chat/completions"
    prompt = (
        "Write an original English YouTube Shorts narration in 85-120 words. Include a hook, a clear explanation, "
        "and a short closing line. Return narration only; no markdown, hashtags, fake citations, or invented precise numbers. "
        "Be cautious about disputed claims. Style: " + style + ". Topic: " + re.sub(r"\s+", " ", topic.strip())[:180]
    )
    body = {"model": model, "messages": [{"role": "system", "content": "Write concise, responsible educational narration."}, {"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 320}
    req = urllib.request.Request(endpoint, data=json.dumps(body).encode("utf-8"), headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=35) as response:
        data = json.loads(response.read().decode("utf-8"))
    text = data["choices"][0]["message"]["content"].strip()
    if text.startswith("```"):
        text = re.sub(r"^\x60{3}(?:text)?\s*|\s*\x60{3}$", "", text, flags=re.I).strip()
    words = re.findall(r"\b[\w'-]+\b", text)
    if not 70 <= len(words) <= 145 or len(text) < 250:
        raise ValueError("AI provider returned a script outside the accepted length/format.")
    return text
