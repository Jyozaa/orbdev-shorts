from __future__ import annotations

import json
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
MAX_COMPLETE_CUTAWAY_VIDEO_SECONDS = 3.4


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
    if concepts:
        result += min(20, len(item_tags & concepts) * 7)

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

    if intent.get("presentation") == "cutaway" and item.get("mediaType") in {"video", "image"}:
        result += 5

    return result


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


def normalize_asset(
    source: Path,
    media_type: str,
    beat_index: int,
    requested_duration: float,
    preserve_complete_video: bool,
) -> tuple[str, float, float, bool]:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    source_duration = duration(source)

    if media_type == "audio":
        output = PUBLIC / f"beat-{beat_index}.mp3"
        render_duration = requested_duration
        if source_duration > 0:
            render_duration = min(render_duration, source_duration)
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-t", str(render_duration), "-af", "loudnorm=I=-15:TP=-1.5:LRA=6",
                "-codec:a", "libmp3lame", "-q:a", "3", str(output)
            ],
            check=True,
        )
        actual = duration(output) or render_duration
        return f"memes/{output.name}", actual, source_duration, actual >= source_duration - 0.08 if source_duration > 0 else False

    if media_type == "video":
        if preserve_complete_video:
            if source_duration <= 0:
                raise ValueError("video duration could not be measured")
            if source_duration > MAX_COMPLETE_CUTAWAY_VIDEO_SECONDS:
                raise ValueError(
                    f"cutaway video is {source_duration:.2f}s; exceeds complete-clip budget "
                    f"of {MAX_COMPLETE_CUTAWAY_VIDEO_SECONDS:.2f}s"
                )
            render_duration = source_duration
        else:
            render_duration = requested_duration
            if source_duration > 0:
                render_duration = min(render_duration, source_duration)

        output = PUBLIC / f"beat-{beat_index}.mp4"
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-t", str(render_duration), "-vf", "scale=1080:-2,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(output)
            ],
            check=True,
        )
        actual = duration(output) or render_duration
        complete = source_duration > 0 and actual >= source_duration - 0.08
        return f"memes/{output.name}", actual, source_duration, complete

    output = PUBLIC / f"beat-{beat_index}.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-vf", "scale=1080:-2", "-frames:v", "1", str(output)
        ],
        check=True,
    )
    return f"memes/{output.name}", requested_duration, source_duration, True


def infer_presentation(intent: dict[str, object], media_type: str) -> str:
    requested = intent.get("presentation", "auto")
    if requested in {"overlay", "cutaway"}:
        return str(requested)

    purpose = str(intent.get("purpose", "reaction"))
    intensity = int(intent.get("intensity", 1))
    if media_type in {"video", "image"} and intensity >= 2 and purpose in {
        "waiting", "punchline", "confusion", "failure", "success", "absurdity", "reaction"
    }:
        return "cutaway"
    return "overlay"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: select_memes.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))["items"]
    chosen_ids: set[str] = set()
    selections: dict[str, object] = {}

    for index, beat in enumerate(story.get("beats", [])):
        intent = beat.get("memeIntent")
        if not intent:
            continue

        candidates = []
        for item in catalog:
            if not item.get("brandSafe", False) or item.get("rightsStatus") != "approved":
                continue
            if item.get("id") in chosen_ids:
                continue
            candidates.append((score(item, intent), item))

        candidates.sort(key=lambda pair: pair[0], reverse=True)
        if not candidates or candidates[0][0] < 50:
            print(f"Beat {index}: no meme passed confidence threshold")
            continue

        selected_result = None
        for value, selected in candidates[:12]:
            path = str(selected["path"])
            repo_name = os.getenv("GITHUB_REPOSITORY", "Jyozaa/orbdev-shorts")
            encoded = urllib.parse.quote(path, safe="/")
            raw_url = f"https://raw.githubusercontent.com/{repo_name}/main/{encoded}"
            temp = BUILD / f"meme-{index}{Path(path).suffix.lower()}"
            try:
                request = urllib.request.Request(raw_url, headers={"User-Agent":"orbdev-renderer"})
                with urllib.request.urlopen(request, timeout=60) as response:
                    temp.write_bytes(response.read())

                media_type = str(selected["mediaType"])
                presentation = infer_presentation(intent, media_type)
                default_duration = 0.85 if media_type == "audio" else (1.35 if presentation == "cutaway" else 1.1)
                requested_duration = float(intent.get("maxDurationSeconds") or default_duration)

                src, normalized_duration, source_duration, complete = normalize_asset(
                    temp,
                    media_type,
                    index,
                    requested_duration,
                    preserve_complete_video=presentation == "cutaway" and media_type == "video",
                )
                selected_result = (
                    value,
                    selected,
                    path,
                    src,
                    normalized_duration,
                    presentation,
                    source_duration,
                    complete,
                )
                break
            except Exception as exc:
                print(f"Beat {index}: candidate failed: {path}: {exc}")
            finally:
                temp.unlink(missing_ok=True)

        if selected_result is None:
            continue

        (
            value,
            selected,
            path,
            src,
            normalized_duration,
            presentation,
            source_duration,
            complete,
        ) = selected_result
        chosen_ids.add(str(selected["id"]))
        selections[str(index)] = {
            "id": selected["id"],
            "sourcePath": path,
            "score": round(value, 2),
            "mediaType": selected["mediaType"],
            "src": src,
            "durationSeconds": round(normalized_duration, 3),
            "sourceDurationSeconds": round(float(source_duration), 3) if source_duration else None,
            "completeClip": bool(complete),
            "volume": 0.64 if selected["mediaType"] == "audio" else (0.78 if presentation == "cutaway" else 0.44),
            "presentation": presentation,
        }
        print(
            f"Beat {index}: selected {path} "
            f"({value:.1f}, {presentation}, complete={bool(complete)})"
        )

    SELECTION.parent.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps(selections, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
