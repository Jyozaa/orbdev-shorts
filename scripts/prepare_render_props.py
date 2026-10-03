from __future__ import annotations

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

    prepared = []
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
            sources = story.get("editorial", {}).get("sources", [])
            if 0 <= raw_source_index < len(sources):
                adjusted["visual"]["publisher"] = sources[raw_source_index].get("publisher", "SOURCE")
            if source_index in source_assets:
                adjusted["visual"]["src"] = source_assets[source_index]

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
            if "meme" not in beat:
                continue
            beat_duration = float(beat["end"]) - float(beat["start"])
            meme = beat["meme"]
            meme_duration = min(float(meme["durationSeconds"]), max(0.20, beat_duration - 0.05))
            meme["durationSeconds"] = round(meme_duration, 3)
            meme["offsetSeconds"] = round(max(0.02, beat_duration - meme_duration - 0.03), 3)

    props = dict(story)
    props["durationSeconds"] = final_duration
    props["beats"] = prepared
    props["captions"] = words
    props["cutaways"] = cutaways

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = BUILD_DIR / "render-props.json"
    output.write_text(json.dumps(props, indent=2), encoding="utf-8")
    print(
        f"Render props ready: {len(prepared)} voice-timed beats, "
        f"{len(cutaways)} cutaways, {final_duration:.2f}s"
    )


if __name__ == "__main__":
    main()
