from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BUILD_DIR = Path("build")
CAPTIONS_PATH = Path("public/captions.json")
MEME_SELECTION_PATH = BUILD_DIR / "meme-selection.json"
SOURCE_ASSETS_PATH = BUILD_DIR / "source-assets.json"


def norm(token: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", token.lower())


def beat_tokens(text: str) -> list[str]:
    return [value for value in (norm(token) for token in re.findall(r"\S+", text)) if value]


def find_sequence(words: list[dict[str, object]], expected: list[str], cursor: int) -> tuple[int, int]:
    normalized = [norm(str(word["text"])) for word in words]
    for start in range(cursor, min(len(words), cursor + 8)):
        end = start + len(expected)
        if normalized[start:end] == expected:
            return start, end - 1
    end = min(len(words) - 1, cursor + max(1, len(expected)) - 1)
    return cursor, end


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_render_props.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    timing = json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))
    words = timing["words"]
    audio_duration = float(timing["durationSeconds"])
    final_duration = max(1.0, audio_duration + 0.10)

    selections = (
        json.loads(MEME_SELECTION_PATH.read_text(encoding="utf-8"))
        if MEME_SELECTION_PATH.exists() else {}
    )
    source_assets = (
        json.loads(SOURCE_ASSETS_PATH.read_text(encoding="utf-8"))
        if SOURCE_ASSETS_PATH.exists() else {}
    )

    prepared = []
    cursor = 0
    for index, beat in enumerate(story["beats"]):
        expected = beat_tokens(beat["text"])
        start_index, end_index = find_sequence(words, expected, cursor)
        cursor = end_index + 1

        adjusted = dict(beat)
        adjusted["visual"] = dict(beat["visual"])
        adjusted["start"] = round(float(words[start_index]["startMs"]) / 1000.0, 4)
        adjusted["end"] = round(float(words[end_index]["endMs"]) / 1000.0, 4)

        if adjusted["visual"].get("type") == "source":
            source_index = str(adjusted["visual"].get("sourceIndex", 0))
            if source_index in source_assets:
                adjusted["visual"]["src"] = source_assets[source_index]

        selected = selections.get(str(index))
        if selected:
            adjusted["meme"] = dict(selected)

        prepared.append(adjusted)

    if prepared:
        prepared[0]["start"] = 0.0
        for index in range(len(prepared) - 1):
            prepared[index]["end"] = prepared[index + 1]["start"]
        prepared[-1]["end"] = final_duration

        for beat in prepared:
            if "meme" in beat:
                beat_duration = float(beat["end"]) - float(beat["start"])
                meme = beat["meme"]
                meme_duration = min(float(meme["durationSeconds"]), max(0.25, beat_duration - 0.08))
                meme["durationSeconds"] = round(meme_duration, 3)
                meme["offsetSeconds"] = round(
                    max(0.03, beat_duration - meme_duration - 0.04), 3
                )

    props = dict(story)
    props["durationSeconds"] = final_duration
    props["beats"] = prepared
    props["captions"] = words

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = BUILD_DIR / "render-props.json"
    output.write_text(json.dumps(props, indent=2), encoding="utf-8")
    print(f"Render props ready: {len(prepared)} voice-timed beats, {final_duration:.2f}s")


if __name__ == "__main__":
    main()
