import re
from datetime import datetime

def clean_topic(topic: str) -> str:
    topic = re.sub(r"\s+", " ", (topic or "").strip())
    return topic[:180] or "One surprising fact about everyday life"

def generate_script(topic: str, style: str = "curiosity") -> str:
    """Reliable local fallback. This is a template, not an LLM-generated factual script."""
    t = clean_topic(topic)
    if style == "story":
        parts = [
            f"What if the story you know about {t} is only half the truth?",
            f"Start with one question: what is the detail about {t} that most people overlook?",
            "That small detail can change how the whole story feels. It is a reminder to check the evidence before accepting a dramatic claim.",
            f"So the next time you hear about {t}, pause, look for a trustworthy source, and ask what the facts actually show.",
            "Follow for more short stories and surprising ideas. And remember: curiosity is better when it is backed by evidence."
        ]
    else:
        parts = [
            f"Here is one question worth asking about {t}.",
            f"Most people hear about {t} and immediately jump to a conclusion. But the useful part is often the detail hiding underneath the headline.",
            "A good way to understand any topic is to separate what is confirmed, what is still uncertain, and what is simply an opinion.",
            f"When you explore {t}, look for reliable sources, compare more than one explanation, and be careful with claims that sound too perfect.",
            "Want more quick ideas explained clearly? Follow for the next Short."
        ]
    return "\n\n".join(parts)

def estimate_seconds(script: str, words_per_minute: int = 150) -> int:
    words = len(re.findall(r"\b[\w'-]+\b", script))
    return max(1, round(words / max(80, words_per_minute) * 60))
