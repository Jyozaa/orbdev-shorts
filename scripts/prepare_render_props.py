from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

BUILD_DIR = Path("build")
CAPTIONS_PATH = Path("public/captions.json")
MEME_SELECTION_PATH = BUILD_DIR / "meme-selection.json"
SOURCE_ASSETS_PATH = BUILD_DIR / "source-assets.json"
LOGO_ASSETS_PATH = BUILD_DIR / "logo-assets.json"
CUTAWAYS_PATH = BUILD_DIR / "cutaways.json"

MIN_VISUAL_SECONDS = 1.80
TARGET_VISUAL_SECONDS = 2.25
MAX_VISUAL_SECONDS = 3.20

SFX_DURATIONS = {
    "whoosh": 0.34,
    "impact": 0.42,
    "scratch": 0.48,
    "tick": 0.10,
}


def norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def beat_tokens(text: str) -> list[str]:
    return [value for value in (norm(token) for token in re.findall(r"\S+", text)) if value]


def find_sequence(words: list[dict[str, object]], expected: list[str], cursor: int) -> tuple[int, int]:
    normalized = [norm(str(word["text"])) for word in words]
    for start in range(cursor, min(len(words), cursor + 10)):
        end = start + len(expected)
        if normalized[start:end] == expected:
            return start, end - 1
    end = min(len(words) - 1, cursor + max(1, len(expected)) - 1)
    return cursor, end


def attach_logos(visual: dict[str, object], logo_assets: dict[str, str]) -> None:
    if visual.get("type") == "logo":
        slug = str(visual.get("slug", "")).lower()
        if slug in logo_assets:
            visual["src"] = logo_assets[slug]
    elif visual.get("type") == "flow":
        nodes = visual.get("nodes", [])
        if not isinstance(nodes, list):
            return
        for node in nodes:
            if not isinstance(node, dict) or node.get("kind") != "logo":
                continue
            slug = str(node.get("slug", "")).lower()
            if slug in logo_assets:
                node["src"] = logo_assets[slug]


def visual_weight(beat: dict[str, object]) -> int:
    kind = str(beat.get("visual", {}).get("type", "text"))
    return {
        "source": 10,
        "network": 9,
        "chart": 9,
        "timeline": 9,
        "logo": 8,
        "comparison": 8,
        "flow": 7,
        "diagram": 7,
        "metric": 5,
        "symbol": 4,
        "text": 2,
    }.get(kind, 1)


def build_visual_windows(
    beats: list[dict[str, object]],
    cutaway_by_beat: dict[int, dict[str, object]],
    final_duration: float,
) -> list[dict[str, object]]:
    windows: list[dict[str, object]] = []
    index = 0

    while index < len(beats):
        start_index = index
        end_index = index
        start = float(beats[index]["start"])
        end = float(beats[index]["end"])

        while end_index + 1 < len(beats):
            if end_index in cutaway_by_beat:
                break

            current_duration = end - start
            if current_duration >= TARGET_VISUAL_SECONDS:
                break

            next_end = float(beats[end_index + 1]["end"])
            proposed = next_end - start

            if proposed > MAX_VISUAL_SECONDS and current_duration >= MIN_VISUAL_SECONDS:
                break

            end_index += 1
            end = next_end

            if end_index in cutaway_by_beat:
                break
            if end - start >= TARGET_VISUAL_SECONDS:
                break

        candidates = list(range(start_index, end_index + 1))
        chosen_index = max(
            candidates,
            key=lambda candidate: (
                visual_weight(beats[candidate]),
                float(beats[candidate]["end"]) - float(beats[candidate]["start"]),
                -candidate,
            ),
        )

        visual_beat = copy.deepcopy(beats[chosen_index])
        visual_beat["start"] = round(start, 4)
        visual_beat["end"] = round(end, 4)
        visual_beat.pop("meme", None)
        visual_beat.pop("memeIntent", None)
        visual_beat.pop("sfx", None)
        windows.append(visual_beat)

        index = end_index + 1

    if len(windows) >= 2:
        last = windows[-1]
        previous = windows[-2]
        last_duration = float(last["end"]) - float(last["start"])
        combined = float(last["end"]) - float(previous["start"])
        if last_duration < MIN_VISUAL_SECONDS and combined <= MAX_VISUAL_SECONDS + 0.35:
            previous["end"] = last["end"]
            if visual_weight(last) > visual_weight(previous):
                previous["visual"] = copy.deepcopy(last["visual"])
                previous["text"] = last["text"]
            windows.pop()

    if windows and float(windows[-1]["end"]) < final_duration:
        windows[-1]["end"] = round(final_duration, 4)

    return windows


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_render_props.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    timing = json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))
    words = timing["words"]
    final_duration = max(1.0, float(timing["durationSeconds"]) + 0.10)

    selections = json.loads(MEME_SELECTION_PATH.read_text(encoding="utf-8")) if MEME_SELECTION_PATH.exists() else {}
    source_assets = json.loads(SOURCE_ASSETS_PATH.read_text(encoding="utf-8")) if SOURCE_ASSETS_PATH.exists() else {}
    logo_assets = json.loads(LOGO_ASSETS_PATH.read_text(encoding="utf-8")) if LOGO_ASSETS_PATH.exists() else {}
    cutaways = json.loads(CUTAWAYS_PATH.read_text(encoding="utf-8")) if CUTAWAYS_PATH.exists() else []
    cutaway_by_beat = {int(item["beatIndex"]): item for item in cutaways}

    prepared: list[dict[str, object]] = []
    cursor = 0

    for index, beat in enumerate(story["beats"]):
        expected = beat_tokens(beat["text"])
        start_index, end_index = find_sequence(words, expected, cursor)
        cursor = end_index + 1

        adjusted = dict(beat)
        adjusted["visual"] = json.loads(json.dumps(beat["visual"]))
        adjusted["start"] = round(float(words[start_index]["startMs"]) / 1000.0, 4)
        adjusted["end"] = round(float(words[end_index]["endMs"]) / 1000.0, 4)

        if adjusted["visual"].get("type") == "source":
            raw_source_index = int(adjusted["visual"].get("sourceIndex", 0))
            source_index = str(raw_source_index)
            variant = max(0, int(adjusted["visual"].get("variant", 0)))
            sources = story.get("editorial", {}).get("sources", [])
            if 0 <= raw_source_index < len(sources):
                adjusted["visual"]["publisher"] = sources[raw_source_index].get("publisher", "SOURCE")

            entry = source_assets.get(source_index)
            if isinstance(entry, str):
                adjusted["visual"]["src"] = entry
            elif isinstance(entry, dict):
                assets = entry.get("assets", [])
                if isinstance(assets, list) and assets:
                    adjusted["visual"]["src"] = assets[variant % len(assets)]

        attach_logos(adjusted["visual"], logo_assets)

        selected = selections.get(str(index))
        if selected and selected.get("presentation") != "cutaway":
            adjusted["meme"] = dict(selected)

        prepared.append(adjusted)

    if prepared:
        prepared[0]["start"] = 0.0
        for index in range(len(prepared) - 1):
            if index in cutaway_by_beat:
                prepared[index]["end"] = float(cutaway_by_beat[index]["start"])
            else:
                prepared[index]["end"] = prepared[index + 1]["start"]

        last_index = len(prepared) - 1
        if last_index in cutaway_by_beat:
            prepared[last_index]["end"] = float(cutaway_by_beat[last_index]["start"])
        else:
            prepared[last_index]["end"] = final_duration

        for beat in prepared:
            start = float(beat["start"])
            end = float(beat["end"])
            beat_duration = max(0.01, end - start)

            sfx = beat.get("sfx")
            if isinstance(sfx, str) and sfx in SFX_DURATIONS:
                final_duration = max(
                    final_duration,
                    start + SFX_DURATIONS[sfx] + 0.08,
                )

            if "meme" not in beat:
                continue

            meme = beat["meme"]
            selected_duration = float(meme["durationSeconds"])
            media_type = str(meme.get("mediaType", ""))

            if media_type == "audio":
                # Preserve the entire short audio reaction. It may naturally
                # spill into the next visual instead of being chopped to this beat.
                meme["durationSeconds"] = round(selected_duration, 3)
                meme["offsetSeconds"] = round(max(0.02, beat_duration - 0.16), 3)
                final_duration = max(
                    final_duration,
                    start + float(meme["offsetSeconds"]) + selected_duration + 0.08,
                )
            else:
                meme_duration = min(selected_duration, max(0.35, beat_duration - 0.05))
                meme["durationSeconds"] = round(meme_duration, 3)
                meme["offsetSeconds"] = round(max(0.02, beat_duration - meme_duration - 0.03), 3)

        if last_index not in cutaway_by_beat:
            prepared[last_index]["end"] = round(final_duration, 4)

    visual_beats = build_visual_windows(prepared, cutaway_by_beat, final_duration)

    props = dict(story)
    props["durationSeconds"] = round(final_duration, 4)
    props["beats"] = prepared
    props["visualBeats"] = visual_beats
    props["captions"] = words
    props["cutaways"] = cutaways

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = BUILD_DIR / "render-props.json"
    output.write_text(json.dumps(props, indent=2), encoding="utf-8")

    visual_durations = [
        round(float(beat["end"]) - float(beat["start"]), 2)
        for beat in visual_beats
    ]
    print(
        f"Render props ready: {len(prepared)} semantic beats -> "
        f"{len(visual_beats)} visual windows, {len(cutaways)} cutaways, "
        f"{final_duration:.2f}s total"
    )
    print(f"Visual hold durations: {visual_durations}")


if __name__ == "__main__":
    main()
