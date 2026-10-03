from __future__ import annotations

import json
import sys
from pathlib import Path

BUILD_DIR = Path("build")
CAPTIONS_PATH = Path("public/captions.json")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: prepare_render_props.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    timing = json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))

    planned = float(story["plannedDurationSeconds"])
    audio_duration = float(timing["durationSeconds"])
    final_duration = max(1.0, audio_duration + 0.45)
    scale = final_duration / planned

    scenes = []
    for scene in story["scenes"]:
        adjusted = dict(scene)
        adjusted["start"] = round(float(scene["start"]) * scale, 4)
        adjusted["end"] = min(
            final_duration,
            round(float(scene["end"]) * scale, 4),
        )
        scenes.append(adjusted)

    if scenes:
        scenes[-1]["end"] = final_duration

    props = dict(story)
    props["durationSeconds"] = final_duration
    props["scenes"] = scenes
    props["captions"] = timing["words"]

    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = BUILD_DIR / "render-props.json"
    output.write_text(json.dumps(props, indent=2), encoding="utf-8")
    print(f"Render props ready: {output}")


if __name__ == "__main__":
    main()
