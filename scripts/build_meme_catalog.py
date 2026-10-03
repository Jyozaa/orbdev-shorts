from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

API_URL = "https://api.github.com/repos/Jyozaa/memes/git/trees/main?recursive=1"
OUT = Path("build/meme-catalog.json")

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg"}
VIDEO_EXTS = {".mp4", ".mov", ".avi", ".wmv", ".webm", ".mkv"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

BLOCKED_TERMS = {
    "nigga", "nigger", "retarded", "faggot", "gay berleezy", "thot",
    "bitch", "sex", "lesbian", "porn", "knife attack", "gun shooting",
}

def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

def add(values: set[str], *items: str) -> None:
    values.update(item for item in items if item)

def infer(path: str, media_type: str) -> dict[str, object]:
    name = normalize(Path(path).stem)
    tags = set(name.split())
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
        add(tags, "waiting", "time", "delay")
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

    if "stonk" in name:
        add(purposes, "success", "contrast", "absurdity")
        tones = {"positive", "deadpan", "confused"}
        add(tags, "money", "price", "stocks", "profit")
        intensity = max(intensity, 2)

    brand_safe = not any(term in name for term in BLOCKED_TERMS)

    return {
        "id": re.sub(r"[^a-z0-9]+", "-", name).strip("-")[:90],
        "path": path,
        "mediaType": media_type,
        "tags": sorted(tags),
        "purposes": sorted(purposes),
        "tones": sorted(tones),
        "intensity": intensity,
        "brandSafe": brand_safe,
        "rightsStatus": "approved",
    }

def main() -> None:
    token = os.getenv("GITHUB_TOKEN", "")
    request = urllib.request.Request(
        API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        tree = json.load(response)["tree"]

    catalog = []
    for item in tree:
        if item.get("type") != "blob":
            continue
        path = item["path"]
        ext = Path(path).suffix.lower()

        if ext in AUDIO_EXTS:
            media_type = "audio"
        elif ext in VIDEO_EXTS:
            media_type = "video"
        elif ext in IMAGE_EXTS:
            media_type = "image"
        else:
            continue

        if not (
            path.startswith("Meme Pack/Meme Sound Effects/")
            or path.startswith("Meme Pack/Meme Videos/")
            or path.startswith("Memes templates -HD-/")
            or path.startswith("Memes templates -HD- 2/")
        ):
            continue

        entry = infer(path, media_type)
        if entry["brandSafe"]:
            catalog.append(entry)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"version": 1, "items": catalog}, indent=2), encoding="utf-8")
    print(f"Cataloged {len(catalog)} meme assets")

if __name__ == "__main__":
    main()
