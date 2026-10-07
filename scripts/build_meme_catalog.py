from __future__ import annotations

import json
import os
import re
import urllib.request
from pathlib import Path

OUT = Path("build/meme-catalog.json")
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".wmv", ".webm", ".mkv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

ROOT_PREFIXES = (
    "Meme Pack/Meme Sound Effects/",
    "Meme Pack/Meme Videos/",
    "Memes templates -HD-/",
    "Memes templates -HD- 2/",
)

BLOCKED_TERMS = {
    "nigga", "nigger", "retarded", "faggot", "gay berleezy", "thot",
    "bitch", "sex", "lesbian", "porn", "knife attack", "gun shooting",
}


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def add(values: set[str], *items: str) -> None:
    values.update(item for item in items if item)


def semantic_contexts(path: str) -> set[str]:
    """Infer broad reaction meaning from the asset's filename and folder.

    Folder names in the meme pack are useful metadata (for example
    "Dumb - Genius" or "Funny - Not funny"). These contexts are deliberately
    broad and deterministic so the runtime selector can reject a tonally-correct
    but semantically-wrong meme.
    """
    text = normalize(path)
    contexts: set[str] = set()

    rules = (
        ("confusion", ("confused", "confusion", "what do you mean", "what did you say", "blinking", "staring", "huh", "nani")),
        ("rejection", ("nope", "denied", "no god", "no no", "not yet", "not okie", "nooo", "wrong answer")),
        ("failure", ("fail", "failure", "wasted", "facepalm", "burnt", "this is fine", "game over", "mission failed", "bad time")),
        ("success", ("victory", "mission passed", "perfect", "woooo yeah", "yeah baby", "happy streamer", "nice", "fanfare", "outstanding move")),
        ("surprise", ("wow", "woah", "oh my god", "omg", "are you serious", "surprised", "nani")),
        ("waiting", ("2000 years", "2 hours later", "few moments later", "meanwhile", "waiting", "jeopardy")),
        ("money", ("stonk", "cash register", "money", "price", "profit", "broke")),
        ("intelligence", ("big brain", "genius", "smart", "iq", "brain", "outsmart", "harvard", "expert", "clever thoughts", "expanding brain")),
        ("comedy", ("laugh", "funny", "clown", "comedy", "haha", "hehe", "joke")),
        ("anger", ("angry", "rage", "frustration", "killing again", "personal attack")),
        ("disgust", ("disgust", "eww", "weird buddy", "creepy", "gross")),
        ("suspicion", ("sus", "imposter", "suspicious", "illuminati", "enemy spotted")),
        ("danger", ("alert", "alarm", "fbi open up", "attack", "horror", "siren", "vengeance")),
        ("calm", ("calm down", "relax", "okay meme", "okay")),
        ("delay", ("slow", "later", "waiting", "long time", "meanwhile")),
        ("old", ("old message", "old computer", "windows 95", "windows 98", "windows xp")),
        ("absurdity", ("wtf", "what the hell", "weird", "trippin", "cursed", "entire circus")),
        ("boredom", ("not interesting", "boring", "sipping soup", "humm")),
    )
    for context, phrases in rules:
        if any(phrase in text for phrase in phrases):
            contexts.add(context)

    if "reactions dumb genius" in text:
        contexts.update({"intelligence", "comparison"})
    if "reactions funny not funny" in text:
        contexts.update({"comedy", "comparison"})
    if "reactions angry wicked" in text:
        contexts.add("anger")
    if "reactions humm not interesting boring" in text:
        contexts.add("boredom")

    return contexts


def infer(path: str, media_type: str) -> dict[str, object]:
    name = normalize(Path(path).stem)
    tags = set(name.split())
    contexts = semantic_contexts(path)
    purposes = {"reaction"}
    tones = {"neutral"}
    intensity = 1

    if any(k in name for k in ["woooo yeah", "wooo", "yeah baby", "happy", "victory", "nice", "confetti", "anime wow", "wow"]):
        add(purposes, "success", "emphasis")
        tones = {"positive", "surprised"}
        add(tags, "celebration", "win", "success", "excitement", "good news")
        intensity = 3 if any(k in name for k in ["woooo", "yeah baby", "victory"]) else 2

    if any(k in name for k in ["bruh", "facepalm", "wrong answer", "eww", "disgusted", "wtf", "what the hell", "dead"]):
        add(purposes, "failure", "punchline")
        tones = {"negative", "deadpan"}
        add(tags, "disbelief", "frustration", "disappointment", "bad news")
        intensity = 2

    if any(k in name for k in ["confused", "confusion", "what do you mean", "what did you say", "are you serious", "staring"]):
        add(purposes, "confusion")
        tones = {"confused", "surprised"}
        add(tags, "confused", "question", "unclear", "disbelief")
        intensity = max(intensity, 2)

    if any(k in name for k in ["2000 years", "2 hours later", "few moments later", "waiting", "meanwhile"]):
        add(purposes, "waiting", "punchline")
        tones = {"deadpan", "awkward"}
        add(tags, "waiting", "time", "delay", "later", "long time")
        intensity = max(intensity, 2)

    if any(k in name for k in ["laugh", "laughter", "haha", "hehe", "giggle"]):
        add(purposes, "reaction", "punchline", "emphasis")
        tones = {"positive", "chaotic", "deadpan"}
        add(tags, "laugh", "laughter", "funny", "comedy", "joke")
        intensity = max(intensity, 2)

    if any(k in name for k in ["this is fine", "burnt", "wasted", "fail", "failure"]):
        add(purposes, "failure", "absurdity")
        tones = {"negative", "deadpan"}
        add(tags, "failure", "disaster", "bad news")
        intensity = max(intensity, 2)

    if any(k in name for k in ["bonk", "boing", "air horn", "bass drop", "boom", "anvil"]):
        add(purposes, "punchline", "emphasis")
        tones.add("chaotic")
        add(tags, "impact", "punchline", "chaotic")
        intensity = max(intensity, 2)

    if "not stonk" in name or "stonk not" in name or "anti stonk" in name:
        add(purposes, "failure", "contrast", "absurdity")
        tones = {"negative", "deadpan"}
        add(tags, "money", "price", "stocks", "loss", "bad news")
        tags.discard("profit")
        intensity = max(intensity, 2)
    elif "confused stonk" in name or "stonks confused" in name:
        add(purposes, "confusion", "contrast", "absurdity")
        tones = {"confused", "deadpan"}
        add(tags, "money", "price", "stocks", "confusion", "unclear")
        intensity = max(intensity, 2)
    elif "stonk" in name:
        add(purposes, "success", "contrast", "absurdity")
        tones = {"positive", "deadpan"}
        add(tags, "money", "price", "stocks", "profit", "win")
        intensity = max(intensity, 2)

    return {
        "id": re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:90],
        "path": path,
        "mediaType": media_type,
        "tags": sorted(tags),
        "purposes": sorted(purposes),
        "tones": sorted(tones),
        "contexts": sorted(contexts),
        "intensity": intensity,
        "brandSafe": not any(term in name for term in BLOCKED_TERMS),
        "rightsStatus": "approved",
    }


def main() -> None:
    repo = os.getenv("GITHUB_REPOSITORY", "Jyozaa/orbdev-shorts")
    token = os.getenv("GITHUB_TOKEN", "")
    api = f"https://api.github.com/repos/{repo}/git/trees/main?recursive=1"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "orbdev-renderer",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(api, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        tree = json.load(response)["tree"]

    catalog = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        if not path.startswith(ROOT_PREFIXES):
            continue

        ext = Path(path).suffix.lower()
        if ext in AUDIO_EXTS:
            media_type = "audio"
        elif ext in VIDEO_EXTS:
            media_type = "video"
        elif ext in IMAGE_EXTS:
            media_type = "image"
        else:
            continue

        entry = infer(path, media_type)
        if entry["brandSafe"]:
            catalog.append(entry)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"version": 7, "source": repo, "items": catalog}, indent=2),
        encoding="utf-8",
    )
    print(f"Cataloged {len(catalog)} meme assets from {repo}")


if __name__ == "__main__":
    main()
