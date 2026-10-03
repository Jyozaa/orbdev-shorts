from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

OUT = Path("build/meme-catalog.json")

MEME_ROOTS = (
    Path("Meme Pack/Meme Sound Effects"),
    Path("Meme Pack/Meme Videos"),
    Path("Memes templates -HD-"),
    Path("Memes templates -HD- 2"),
)

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


def media_type_for(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext in AUDIO_EXTS:
        return "audio"
    if ext in VIDEO_EXTS:
        return "video"
    if ext in IMAGE_EXTS:
        return "image"
    return None


def infer(path: Path, media_type: str) -> dict[str, object]:
    relative_path = path.as_posix()
    name = normalize(path.stem)
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
    suffix = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:8]

    return {
        "id": f"{re.sub(r'[^a-z0-9]+', '-', name).strip('-')[:72]}-{suffix}",
        "path": relative_path,
        "mediaType": media_type,
        "tags": sorted(tags),
        "purposes": sorted(purposes),
        "tones": sorted(tones),
        "intensity": intensity,
        "brandSafe": brand_safe,
        "rightsStatus": "approved",
    }


def main() -> None:
    catalog = []

    for root in MEME_ROOTS:
        if not root.is_dir():
            print(f"Skipping missing meme folder: {root}")
            continue

        for path in root.rglob("*"):
            if not path.is_file():
                continue

            media_type = media_type_for(path)
            if media_type is None:
                continue

            entry = infer(path, media_type)
            if entry["brandSafe"]:
                catalog.append(entry)

    catalog.sort(key=lambda item: str(item["path"]).lower())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps({"version": 2, "source": "local", "items": catalog}, indent=2),
        encoding="utf-8",
    )
    print(f"Cataloged {len(catalog)} local meme assets")


if __name__ == "__main__":
    main()
