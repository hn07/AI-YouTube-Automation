"""Optional RSS topic discovery with source URLs and duplicate suppression.

This module is deliberately separate from the default daily workflow. RSS headlines
are leads for human review, not verified facts. Uses only Python standard library.
"""
import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output"
HISTORY = OUT / "researched_topic_history.json"
CANDIDATES = OUT / "researched_topic_candidates.json"
DEFAULT_FEEDS = [
    "https://www.nasa.gov/news-release/feed/",
    "https://www.sciencedaily.com/rss/top/science.xml",
]
MAX_FEED_BYTES = 2_000_000
MAX_PER_FEED = 25
USER_AGENT = "AI-YouTube-Automation/1.6 (+RSS topic discovery)"


def _local_name(tag):
    return tag.rsplit("}", 1)[-1].lower()


def _clean(value):
    return re.sub(r"\\s+", " ", (value or "")).strip()


def _load_history():
    try:
        data = json.loads(HISTORY.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _parse_feed(xml_bytes, feed_url):
    root = ET.fromstring(xml_bytes)
    entries = []
    # RSS <item> and Atom <entry>, namespace independent.
    for node in root.iter():
        if _local_name(node.tag) not in ("item", "entry"):
            continue
        fields = {}
        for child in list(node):
            name = _local_name(child.tag)
            if name == "link":
                href = child.attrib.get("href") or (child.text or "")
                fields["link"] = href.strip()
            elif name in ("title", "description", "summary", "pubdate", "published", "updated"):
                fields[name] = _clean(" ".join(child.itertext()))
        title = fields.get("title", "")
        link = fields.get("link", "")
        if not title or not link:
            continue
        parsed = urlparse(link)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            continue
        entries.append({
            "topic": title[:180],
            "source_url": link,
            "source_feed": feed_url,
            "published": fields.get("pubdate") or fields.get("published") or fields.get("updated") or "",
            "summary": fields.get("description") or fields.get("summary", "")[:600],
        })
        if len(entries) >= MAX_PER_FEED:
            break
    return entries


def discover_topics(feed_urls=None, limit=20, timeout=12):
    """Fetch RSS/Atom feeds, deduplicate against prior discoveries, save review queue."""
    OUT.mkdir(parents=True, exist_ok=True)
    feeds = feed_urls or [x.strip() for x in os.getenv("TOPIC_RSS_FEEDS", "").split(",") if x.strip()] or DEFAULT_FEEDS
    history = _load_history()
    seen = {str(x.get("key", "")) for x in history if isinstance(x, dict)}
    candidates = []
    errors = []
    for feed in feeds[:10]:
        try:
            request = urllib.request.Request(feed, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                final_url = response.geturl()
                if urlparse(final_url).scheme != "https":
                    raise ValueError("Feed redirects to a non-HTTPS URL; blocked")
                body = response.read(MAX_FEED_BYTES + 1)
            if len(body) > MAX_FEED_BYTES:
                raise ValueError("Feed exceeds 2 MB safety limit")
            for entry in _parse_feed(body, feed):
                key = hashlib.sha256((entry["topic"].casefold().strip() + "|" + entry["source_url"]).encode("utf-8")).hexdigest()
                if key in seen:
                    continue
                entry["key"] = key
                entry["discovered_at"] = datetime.now(timezone.utc).isoformat()
                candidates.append(entry)
                seen.add(key)
        except Exception as exc:
            errors.append({"feed": feed, "error": str(exc)[:240]})
    candidates = candidates[:max(1, min(int(limit), 100))]
    CANDIDATES.write_text(json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates), "items": candidates, "feed_errors": errors,
        "review_note": "RSS headlines are leads only. Verify claims from primary sources before publishing."},
        ensure_ascii=False, indent=2), encoding="utf-8")
    return candidates


def mark_reviewed(items):
    """Record reviewed candidate keys to avoid suggesting them again."""
    OUT.mkdir(parents=True, exist_ok=True)
    history = _load_history()
    known = {str(x.get("key", "")) for x in history if isinstance(x, dict)}
    now = datetime.now(timezone.utc).isoformat()
    for item in items:
        key = item.get("key")
        if key and key not in known:
            history.append({"key": key, "topic": item.get("topic", ""), "reviewed_at": now})
            known.add(key)
    HISTORY.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(history)
