from __future__ import annotations

import json
import math
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BUILD = Path("build")
PUBLIC = Path("public/memes")
CATALOG = BUILD / "meme-catalog.json"
SELECTION = BUILD / "meme-selection.json"

def tokens(values: list[str] | None) -> set[str]:
    if not values:
        return set()
    output: set[str] = set()
    for value in values:
        output.update(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
    return output

def score(item: dict[str, object], intent: dict[str, object]) -> float:
    purposes = set(item.get("purposes", []))
    tones = set(item.get("tones", []))
    item_tags = tokens(item.get("tags", []))
    concepts = tokens(intent.get("concepts", []))

    result = 0.0
    if intent.get("purpose") in purposes:
        result += 35
    if intent.get("tone") in tones:
        result += 25

    overlap = len(item_tags & concepts)
    if concepts:
        result += min(20, overlap * 7)

    preferred = intent.get("preferredMedia", "any")
    if preferred == "any":
        result += 5
    elif item.get("mediaType") == preferred:
        result += 10
    else:
        result -= 8

    intensity = int(intent.get("intensity", 1))
    item_intensity = int(item.get("intensity", 1))
    result += max(0, 5 - 2 * abs(intensity - item_intensity))

    name = " ".join(item_tags)
    for concept in concepts:
        if concept in name:
            result += 2

    return result

def download(url: str, target: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "orbdev-renderer"})
    with urllib.request.urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())

def duration(path: Path) -> float:
    try:
        value = subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1", str(path)
            ],
            text=True,
        ).strip()
        return float(value)
    except Exception:
        return 0.0

def normalize_asset(source: Path, media_type: str, scene_index: int, max_duration: float) -> tuple[str, float]:
    PUBLIC.mkdir(parents=True, exist_ok=True)

    if media_type == "audio":
        output = PUBLIC / f"scene-{scene_index}.mp3"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-t", str(max_duration), "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
                "-codec:a", "libmp3lame", "-q:a", "3", str(output)
            ],
            check=True,
        )
        return f"memes/{output.name}", min(max_duration, duration(output) or max_duration)

    if media_type == "video":
        output = PUBLIC / f"scene-{scene_index}.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-t", str(max_duration),
                "-vf", "scale=840:-2:force_original_aspect_ratio=decrease,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
                str(output)
            ],
            check=True,
        )
        return f"memes/{output.name}", min(max_duration, duration(output) or max_duration)

    output = PUBLIC / f"scene-{scene_index}.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-vf", "scale=840:-2:force_original_aspect_ratio=decrease",
            "-frames:v", "1", str(output)
        ],
        check=True,
    )
    return f"memes/{output.name}", max_duration

def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: select_memes.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
    chosen_ids: set[str] = set()
    selections: dict[str, object] = {}

    for index, scene in enumerate(story.get("scenes", [])):
        intent = scene.get("memeIntent")
        if not intent:
            continue

        candidates = []
        for item in catalog:
            if not item.get("brandSafe", False) or item.get("rightsStatus") != "approved":
                continue
            if item.get("id") in chosen_ids:
                continue
            value = score(item, intent)
            candidates.append((value, item))

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        if not candidates or candidates[0][0] < 50:
            print(f"Scene {index}: no meme passed confidence threshold")
            continue

        value, selected = candidates[0]
        chosen_ids.add(selected["id"])
        path = selected["path"]
        encoded = urllib.parse.quote(path, safe="/")
        raw_url = f"https://raw.githubusercontent.com/Jyozaa/memes/main/{encoded}"

        BUILD.mkdir(parents=True, exist_ok=True)
        temp = BUILD / f"meme-{index}{Path(path).suffix.lower()}"
        download(raw_url, temp)

        max_duration = float(intent.get("maxDurationSeconds") or (1.2 if selected["mediaType"] == "audio" else 1.8))
        src, normalized_duration = normalize_asset(temp, selected["mediaType"], index, max_duration)
        temp.unlink(missing_ok=True)

        scene_duration = float(scene["end"]) - float(scene["start"])
        offset = max(0.15, scene_duration - normalized_duration - 0.28)

        selections[str(index)] = {
            "id": selected["id"],
            "sourcePath": path,
            "score": round(value, 2),
            "mediaType": selected["mediaType"],
            "src": src,
            "durationSeconds": round(normalized_duration, 3),
            "offsetSeconds": round(offset, 3),
            "volume": 0.56 if selected["mediaType"] == "audio" else 0.40,
        }
        print(f"Scene {index}: selected {path} ({value:.1f})")

    SELECTION.parent.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps(selections, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
