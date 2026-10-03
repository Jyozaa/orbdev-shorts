from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_TYPES = {"hook", "explain", "metric", "diagram", "comparison", "impact", "caveat", "outro"}
ALLOWED_SFX = {"scratch", "impact", "whoosh", "tick", "none"}
ALLOWED_PURPOSES = {"reaction", "punchline", "contrast", "confusion", "failure", "success", "waiting", "absurdity", "emphasis"}
ALLOWED_TONES = {"positive", "negative", "surprised", "confused", "awkward", "deadpan", "chaotic", "neutral"}
ALLOWED_MEDIA = {"audio", "image", "video", "any"}


def fail(message: str) -> None:
    raise SystemExit(f"Story validation failed: {message}")


def validate_editorial(data: dict[str, object]) -> None:
    editorial = data.get("editorial")
    if not isinstance(editorial, dict):
        fail("current story needs editorial metadata")

    story_key = editorial.get("storyKey")
    if not isinstance(story_key, str) or not story_key.strip():
        fail("editorial.storyKey is required")

    selected_at = editorial.get("selectedAt")
    if not isinstance(selected_at, str) or "T" not in selected_at:
        fail("editorial.selectedAt must be an ISO-8601 timestamp")

    score = editorial.get("score")
    if not isinstance(score, (int, float)) or score < 0 or score > 10:
        fail("editorial.score must be between 0 and 10")

    sources = editorial.get("sources")
    if not isinstance(sources, list) or not sources:
        fail("editorial.sources must contain at least one source")

    has_primary = False
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"editorial source {index} must be an object")
        url = source.get("url")
        if not isinstance(url, str):
            fail(f"editorial source {index} needs a URL")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            fail(f"editorial source {index} needs a valid HTTPS URL")
        if source.get("primary") is True:
            has_primary = True

    if not has_primary:
        fail("at least one editorial source must be primary")

    publish = data.get("publish")
    if not isinstance(publish, dict):
        fail("current story needs publish metadata")
    if not isinstance(publish.get("youtubeTitle"), str) or not publish["youtubeTitle"].strip():
        fail("publish.youtubeTitle is required")
    if publish.get("madeForKids") is not False:
        fail("publish.madeForKids must be false")


def validate_meme_intent(intent: object, scene_index: int) -> None:
    if not isinstance(intent, dict):
        fail(f"scene {scene_index} memeIntent must be an object")
    if intent.get("purpose") not in ALLOWED_PURPOSES:
        fail(f"scene {scene_index} has invalid meme purpose")
    if intent.get("tone") not in ALLOWED_TONES:
        fail(f"scene {scene_index} has invalid meme tone")
    if intent.get("intensity") not in {1, 2, 3}:
        fail(f"scene {scene_index} meme intensity must be 1, 2, or 3")
    if intent.get("preferredMedia") is not None and intent.get("preferredMedia") not in ALLOWED_MEDIA:
        fail(f"scene {scene_index} has invalid preferred meme media")
    if intent.get("maxDurationSeconds") is not None:
        value = intent["maxDurationSeconds"]
        if not isinstance(value, (int, float)) or value <= 0 or value > 3:
            fail(f"scene {scene_index} max meme duration must be between 0 and 3 seconds")


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
    meme_count = 0
    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            fail(f"scene {index} must be an object")
        if scene.get("type") not in ALLOWED_TYPES:
            fail(f"scene {index} has an unsupported type")
        if not isinstance(scene.get("title"), str) or not scene["title"].strip():
            fail(f"scene {index} needs a title")
        if scene.get("sfx") is not None and scene.get("sfx") not in ALLOWED_SFX:
            fail(f"scene {index} has an unsupported sfx")

        if scene.get("memeIntent") is not None:
            validate_meme_intent(scene["memeIntent"], index)
            meme_count += 1

        if scene.get("type") == "diagram":
            nodes = scene.get("nodes")
            if not isinstance(nodes, list) or len(nodes) < 2 or len(nodes) > 4:
                fail(f"diagram scene {index} needs 2 to 4 nodes")
            for node_index, node in enumerate(nodes):
                if not isinstance(node, dict) or not isinstance(node.get("symbol"), str) or not node["symbol"].strip():
                    fail(f"diagram scene {index} node {node_index} needs a symbol")

        start = scene.get("start")
        end = scene.get("end")
        if not isinstance(start, (int, float)) or not isinstance(end, (int, float)):
            fail(f"scene {index} needs numeric start and end values")
        if start < 0 or end <= start:
            fail(f"scene {index} has an invalid time range")
        if abs(float(start) - previous_end) > 0.001:
            fail(f"scene {index} must start where the previous scene ends")
        previous_end = float(end)

    if meme_count > 2:
        fail("normal Shorts may contain at most two meme moments")

    if abs(previous_end - float(planned)) > 0.5:
        fail("scene timeline must end at plannedDurationSeconds")

    if path.name == "current.json":
        validate_editorial(data)

    print(f"Validated {path} with {len(scenes)} scenes and {meme_count} meme intents")


if __name__ == "__main__":
    main()
