"""No-API topic generator for daily English Shorts.

Topics are drawn from curated evergreen prompts and persisted to avoid repeating
recent topics. This does not browse the web or fact-check factual claims.
"""
import json
import random
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "output" / "topic_history.json"

TOPICS = [
    "Why do we dream?", "Why does time feel faster as we get older?", "Why do onions make us cry?",
    "Why do cats purr?", "Why do dogs tilt their heads?", "Why does the Moon look bigger near the horizon?",
    "Why is the ocean salty?", "Why is the sky blue?", "Why do we get goosebumps?",
    "Why do fingerprints differ?", "Why do we yawn when other people yawn?", "Why do we hiccup?",
    "Why do we forget dreams so quickly?", "Why does music give us chills?", "Why do magnets attract some metals?",
    "How do bees communicate?", "How do octopuses camouflage?", "How do migratory birds navigate?",
    "How do fireflies produce light?", "How do trees communicate through chemical signals?",
    "How do sharks detect electrical signals?", "How do chameleons change color?",
    "How do ants find their way home?", "How do spiders make silk?", "How do plants turn toward light?",
    "What happens inside a black hole?", "What is a neutron star?", "Could a planet rain diamonds?",
    "Why is Venus hotter than Mercury?", "How far away is the edge of the observable universe?",
    "What would happen if Earth stopped spinning?", "What makes a solar eclipse possible?",
    "Why does Mars look red?", "How do astronauts sleep in space?", "What is dark matter?",
    "Why do deep oceans stay dark?", "What lives around hydrothermal vents?", "How deep is the deepest ocean point?",
    "What causes bioluminescence in the sea?", "Why can some sea creatures survive extreme pressure?",
    "What is the largest living structure on Earth?", "Why do waves glow blue sometimes?",
    "What happens when lightning strikes sand?", "Why do deserts get cold at night?",
    "How do glaciers shape landscapes?", "What causes a rainbow?", "Why do some lakes look pink?",
    "Why do volcanoes erupt?", "How are caves formed?", "What makes thunder sound different each time?",
    "Why do we have different blood types?", "How does the brain form a memory?", "Why does spicy food feel hot?",
    "Why do fingerprints help identify people?", "How does the body heal a cut?", "Why does laughter spread?",
    "What is déjà vu?", "Why do we dream in stories?", "How does your inner ear help with balance?",
    "Why do humans get goosebumps?", "What happens when you hold your breath?",
    "Why do some animals play dead?", "How do geckos climb walls?", "Why do flamingos look pink?",
    "How can camels conserve water?", "Why do penguins huddle together?", "How do bats navigate in darkness?",
    "Why do crows remember faces?", "How do dolphins sleep?", "Why do some animals glow in the dark?",
    "What makes honey last so long when stored properly?", "Why does popcorn pop?", "Why does metal feel colder than wood?",
    "Why do bubbles look rainbow-colored?", "How does a microwave heat food?", "Why does ice float on water?",
    "Why do airplane windows have rounded corners?", "Why do bridges have expansion joints?",
    "How does noise-cancelling technology work?", "Why do phone batteries age?",
    "How does GPS estimate your location?", "Why do airplane trails sometimes linger?",
    "Why do mirrors reverse left and right only seemingly?", "How does a barcode store information?",
    "Why do some sounds make us uncomfortable?", "How does a solar panel make electricity?",
    "Why do soap bubbles form spheres?", "What causes static electricity?",
    "Why do stars twinkle but planets usually twinkle less?", "How do scientists estimate the age of fossils?",
    "What is the difference between weather and climate?", "Why do some rocks contain crystals?",
    "How do scientists detect exoplanets?", "Why do leaves change color in autumn?",
    "What makes a meteor different from a meteorite?", "How do coral reefs support ocean life?",
]

def generate_daily_topics(count=3):
    ROOT.joinpath("output").mkdir(parents=True, exist_ok=True)
    try:
        history = json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else []
        if not isinstance(history, list):
            history = []
    except Exception:
        history = []
    used = {str(item.get("topic", "")) for item in history if isinstance(item, dict)}
    pool = [topic for topic in TOPICS if topic not in used]
    if len(pool) < count:
        # Begin a new rotation only after all curated topics have been used.
        used.clear()
        pool = TOPICS[:]
    chosen = random.SystemRandom().sample(pool, min(count, len(pool)))
    today = datetime.now().astimezone().date().isoformat()
    history.extend({"date": today, "topic": topic} for topic in chosen)
    HISTORY.write_text(json.dumps(history[-500:], ensure_ascii=False, indent=2), encoding="utf-8")
    return chosen
