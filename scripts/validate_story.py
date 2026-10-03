from __future__ import annotations

import json
import sys
from pathlib import Path

ALLOWED_TYPES = {"hook", "explain", "comparison", "impact", "caveat", "outro"}


def fail(message: str) -> None:
    raise SystemExit(f"Story validation failed: {message}")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_story.py <story.json>")

    path = Path(sys.argv[1])
    if not path.is_file():
        fail(f"file not found: {path}")

    data = json.loads(path.read_text(encoding="utf-8"))

    for key in ("slug", "title", "narration", "plannedDurationSeconds", "scenes"):
        if key not in data:
            fail(f"missing field: {key}")

    if not isinstance(data["narration"], str) or len(data["narration"].strip()) < 10:
        fail("narration must contain usable text")

    planned = data["plannedDurationSeconds"]
    if not isinstance(planned, (int, float)) or planned <= 0 or planned > 90:
        fail("plannedDurationSeconds must be between 0 and 90")

    scenes = data["scenes"]
    if not isinstance(scenes, list) or not scenes:
        fail("scenes must be a non-empty list")

    previous_end = 0.0
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            fail(f"scene {index} must be an object")
        if scene.get("type") not in ALLOWED_TYPES:
            fail(f"scene {index} has an unsupported type")
        if not isinstance(scene.get("title"), str) or not scene["title"].strip():
            fail(f"scene {index} needs a title")

        start = scene.get("start")
        end = scene.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            fail(f"scene {index} needs numeric start and end values")
        if start < 0 or end <= start:
            fail(f"scene {index} has an invalid time range")
        if start < previous_end - 0.001:
            fail(f"scene {index} overlaps the previous scene")
        previous_end = float(end)

    if previous_end > float(planned) + 0.5:
        fail("scene timeline exceeds plannedDurationSeconds")

    print(f"Validated {path} with {len(scenes)} scenes")


if __name__ == "__main__":
    main()
