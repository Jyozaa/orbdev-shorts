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
MAX_COMPLETE_AUDIO_OVERLAY_SECONDS = 2.2
MAX_MEME_MOMENTS = 6

REACTION_CUES = (
    (r"\b(headline )?sounds? wild\b|\bthis is wild\b|\bkind of insane\b|\bpretty insane\b|\bsounds? insane\b",
     {"purpose":"reaction","tone":"surprised","intensity":2,"preferredMedia":"any","presentation":"overlay",
      "concepts":["wow","surprised","disbelief","reaction"]}),
    (r"\bgets? weird\b|\bthis is weird\b|\bgets? strange\b",
     {"purpose":"confusion","tone":"confused","intensity":2,"preferredMedia":"any","presentation":"overlay",
      "concepts":["confused","question","what do you mean","disbelief"]}),
    (r"\bsounds? great\b|\bgreat news\b|\bgood news\b",
     {"purpose":"success","tone":"positive","intensity":1,"preferredMedia":"any","presentation":"overlay",
      "concepts":["nice","success","celebration","good news"]}),
)


def tokens(values: list[str] | None) -> set[str]:
    if not values:
        return set()
    output: set[str] = set()
    for value in values:
        output.update(re.sub(r"[^a-z0-9]+", " ", value.lower()).split())
    return output


def automatic_intent(text: str, editorial_role: str = "") -> dict[str, object] | None:
    role=editorial_role.strip().lower()
    role_intents={
        "joke":{"purpose":"punchline","tone":"deadpan","intensity":2,"preferredMedia":"image","presentation":"overlay","concepts":["reaction","laugh","disbelief","funny"]},
        "reaction":{"purpose":"reaction","tone":"surprised","intensity":2,"preferredMedia":"image","presentation":"overlay","concepts":["reaction","wow","disbelief"]},
        "analogy":{"purpose":"contrast","tone":"surprised","intensity":1,"preferredMedia":"image","presentation":"overlay","concepts":["comparison","reaction","confused"]},
        "punchline":{"purpose":"punchline","tone":"chaotic","intensity":2,"preferredMedia":"any","presentation":"overlay","concepts":["laugh","reaction","funny","win"]},
        "callback":{"purpose":"punchline","tone":"positive","intensity":2,"preferredMedia":"image","presentation":"overlay","concepts":["reaction","win","laugh"]},
    }
    if role in role_intents:return dict(role_intents[role])
    lowered=text.lower().replace("’", "'")
    for pattern,intent in REACTION_CUES:
        if re.search(pattern,lowered,flags=re.I):return dict(intent)
    return None


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
        result += 9 if item.get("mediaType") in {"image","video"} else 2
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


def has_audio_stream(path: Path) -> bool:
    try:
        value = subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "a",
                "-show_entries", "stream=index", "-of", "csv=p=0", str(path)
            ],
            text=True,
        ).strip()
        return bool(value)
    except Exception:
        return False


def normalize_asset(
    source: Path,
    media_type: str,
    beat_index: int,
    requested_duration: float,
    preserve_complete_video: bool,
) -> tuple[str, float, float, bool, bool]:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    source_duration = duration(source)
    source_has_audio = media_type == "audio" or (media_type == "video" and has_audio_stream(source))

    if media_type == "audio":
        if source_duration <= 0:
            raise ValueError("audio duration could not be measured")
        if source_duration > MAX_COMPLETE_AUDIO_OVERLAY_SECONDS:
            raise ValueError(
                f"audio reaction is {source_duration:.2f}s; exceeds complete-audio budget "
                f"of {MAX_COMPLETE_AUDIO_OVERLAY_SECONDS:.2f}s"
            )

        output = PUBLIC / f"beat-{beat_index}.mp3"
        render_duration = source_duration
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-t", str(render_duration), "-af", "loudnorm=I=-15:TP=-1.5:LRA=6",
                "-codec:a", "libmp3lame", "-q:a", "3", str(output)
            ],
            check=True,
        )
        actual = duration(output) or render_duration
        complete = actual >= source_duration - 0.08
        return f"memes/{output.name}", actual, source_duration, complete, True

    if media_type == "video":
        if preserve_complete_video:
            if not source_has_audio:
                raise ValueError("standalone cutaway video has no audio")
            if source_duration <= 0:
                raise ValueError("video duration could not be measured")
            if source_duration > MAX_COMPLETE_CUTAWAY_VIDEO_SECONDS:
                raise ValueError(
                    f"cutaway video is {source_duration:.2f}s; exceeds complete-clip budget "
                    f"of {MAX_COMPLETE_CUTAWAY_VIDEO_SECONDS:.2f}s"
                )
            render_duration = source_duration
        else:
            render_duration = min(requested_duration, source_duration) if source_duration > 0 else requested_duration

        output = PUBLIC / f"beat-{beat_index}.mp4"
        command = [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-t", str(render_duration), "-vf", "scale=1080:-2,fps=30",
            "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        ]
        if source_has_audio:
            command += ["-c:a", "aac", "-b:a", "160k"]
        else:
            command += ["-an"]
        command += ["-movflags", "+faststart", str(output)]
        subprocess.run(command, check=True)
        actual = duration(output) or render_duration
        complete = source_duration > 0 and actual >= source_duration - 0.08
        return f"memes/{output.name}", actual, source_duration, complete, source_has_audio

    output = PUBLIC / f"beat-{beat_index}.png"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-vf", "scale=1080:-2", "-frames:v", "1", str(output)
        ],
        check=True,
    )
    return f"memes/{output.name}", requested_duration, source_duration, True, False


def desired_presentation(intent: dict[str, object], media_type: str) -> str:
    requested = str(intent.get("presentation", "auto"))
    if requested == "overlay":
        return "overlay"
    if requested == "cutaway":
        return "cutaway" if media_type == "video" else "overlay"

    purpose = str(intent.get("purpose", "reaction"))
    intensity = int(intent.get("intensity", 1))
    if media_type == "video" and intensity >= 2 and purpose in {
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

    explicit_count = sum(1 for beat in story.get("beats", []) if beat.get("memeIntent"))
    auto_slots = max(0, MAX_MEME_MOMENTS - explicit_count)
    last_auto_index = -99

    for index, beat in enumerate(story.get("beats", [])):
        explicit = beat.get("memeIntent")
        intent_source = "explicit"
        intent = explicit

        if not intent and auto_slots > 0 and index - last_auto_index >= 2:
            inferred = automatic_intent(str(beat.get("text", "")), str(beat.get("editorialRole", "")))
            if inferred:
                intent = inferred
                intent_source = "auto-cue"

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
        for value, selected in candidates[:14]:
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
                presentation = desired_presentation(intent, media_type)

                if media_type == "video" and presentation == "cutaway" and not has_audio_stream(temp):
                    presentation = "overlay"

                default_duration = 0.75 if media_type == "audio" else (1.25 if presentation == "cutaway" else 1.0)
                requested_duration = float(intent.get("maxDurationSeconds") or default_duration)

                src, normalized_duration, source_duration, complete, has_audio = normalize_asset(
                    temp,
                    media_type,
                    index,
                    requested_duration,
                    preserve_complete_video=presentation == "cutaway",
                )
                selected_result = (
                    value, selected, path, src, normalized_duration,
                    presentation, source_duration, complete, has_audio
                )
                break
            except Exception as exc:
                print(f"Beat {index}: candidate failed: {path}: {exc}")
            finally:
                temp.unlink(missing_ok=True)

        if selected_result is None:
            continue

        (
            value, selected, path, src, normalized_duration,
            presentation, source_duration, complete, has_audio
        ) = selected_result

        if presentation == "cutaway" and not (selected["mediaType"] == "video" and has_audio):
            presentation = "overlay"

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
            "hasAudio": bool(has_audio),
            "volume": 0.64 if selected["mediaType"] == "audio" else (0.78 if presentation == "cutaway" else 0.40),
            "presentation": presentation,
            "intentSource": intent_source,
        }
        chosen_ids.add(str(selected["id"]))

        if intent_source == "auto-cue":
            auto_slots -= 1
            last_auto_index = index

        print(
            f"Beat {index}: selected {path} "
            f"({value:.1f}, {presentation}, audio={bool(has_audio)}, intent={intent_source})"
        )

    SELECTION.parent.mkdir(parents=True, exist_ok=True)
    SELECTION.write_text(json.dumps(selections, indent=2), encoding="utf-8")
    visible=sum(1 for item in selections.values() if item.get("mediaType")!="audio")
    audio=sum(1 for item in selections.values() if item.get("mediaType")=="audio")
    print(f"Meme mix: {visible} visible overlays/cutaways + {audio} audio reactions")


if __name__ == "__main__":
    main()
