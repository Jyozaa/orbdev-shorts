from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_VISUALS = {"source", "metric", "diagram", "comparison", "symbol", "text"}
ALLOWED_SFX = {"scratch", "impact", "whoosh", "tick", "none"}
ALLOWED_PURPOSES = {"reaction", "punchline", "contrast", "confusion", "failure", "success", "waiting", "absurdity", "emphasis"}
ALLOWED_TONES = {"positive", "negative", "surprised", "confused", "awkward", "deadpan", "chaotic", "neutral"}
ALLOWED_MEDIA = {"audio", "image", "video", "any"}
ALLOWED_PRESENTATIONS = {"auto", "overlay", "cutaway"}


def fail(message: str) -> None:
    raise SystemExit(f"Story validation failed: {message}")


def normalized_space(text: str) -> str:
    return " ".join(text.split())


def validate_editorial(data: dict[str, object]) -> None:
    editorial = data.get("editorial")
    if not isinstance(editorial, dict):
        fail("current story needs editorial metadata")
    for key in ("storyKey", "selectedAt", "score", "sources"):
        if key not in editorial:
            fail(f"editorial.{key} is required")
    score = editorial["score"]
    if not isinstance(score, (int, float)) or not 0 <= score <= 10:
        fail("editorial.score must be between 0 and 10")
    sources = editorial["sources"]
    if not isinstance(sources, list) or not sources:
        fail("editorial.sources must contain at least one source")
    has_primary = False
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            fail(f"source {index} must be an object")
        url = source.get("url")
        if not isinstance(url, str):
            fail(f"source {index} needs a URL")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.netloc:
            fail(f"source {index} needs a valid HTTPS URL")
        has_primary = has_primary or source.get("primary") is True
    if not has_primary:
        fail("at least one source must be primary")


def validate_meme_intent(intent: object, beat_index: int) -> None:
    if not isinstance(intent, dict):
        fail(f"beat {beat_index} memeIntent must be an object")
    if intent.get("purpose") not in ALLOWED_PURPOSES:
        fail(f"beat {beat_index} has invalid meme purpose")
    if intent.get("tone") not in ALLOWED_TONES:
        fail(f"beat {beat_index} has invalid meme tone")
    if intent.get("intensity") not in {1, 2, 3}:
        fail(f"beat {beat_index} meme intensity must be 1, 2, or 3")
    if intent.get("preferredMedia") is not None and intent.get("preferredMedia") not in ALLOWED_MEDIA:
        fail(f"beat {beat_index} has invalid meme media")
    if intent.get("presentation") is not None and intent.get("presentation") not in ALLOWED_PRESENTATIONS:
        fail(f"beat {beat_index} has invalid meme presentation")
    if intent.get("maxDurationSeconds") is not None:
        value = intent["maxDurationSeconds"]
        if not isinstance(value, (int, float)) or value <= 0 or value > 3:
            fail(f"beat {beat_index} max meme duration must be between 0 and 3 seconds")


def main() -> None:
    if len(sys.argv) != 2:
        fail("usage: validate_story.py <story.json>")

    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))

    for key in ("slug", "title", "narration", "beats"):
        if key not in data:
            fail(f"missing field: {key}")

    narration = data["narration"]
    if not isinstance(narration, str) or len(narration.strip()) < 10:
        fail("narration must contain usable text")

    beats = data["beats"]
    if not isinstance(beats, list) or not 8 <= len(beats) <= 24:
        fail("beats must contain between 8 and 24 voice-first beats")

    meme_count = 0
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            fail(f"beat {index} must be an object")
        text = beat.get("text")
        if not isinstance(text, str) or not text.strip():
            fail(f"beat {index} needs exact narration text")
        if len(re.findall(r"\S+", text)) > 12:
            fail(f"beat {index} is too long; split it into a faster visual beat")

        visual = beat.get("visual")
        if not isinstance(visual, dict) or visual.get("type") not in ALLOWED_VISUALS:
            fail(f"beat {index} has an invalid visual")

        kind = visual["type"]
        if kind == "source":
            if not isinstance(visual.get("sourceIndex"), int) or visual["sourceIndex"] < 0:
                fail(f"beat {index} source visual needs sourceIndex")
        elif kind == "metric":
            if not isinstance(visual.get("value"), str) or not visual["value"].strip():
                fail(f"beat {index} metric needs value")
        elif kind == "diagram":
            symbols = visual.get("symbols")
            if not isinstance(symbols, list) or not 2 <= len(symbols) <= 4:
                fail(f"beat {index} diagram needs 2-4 symbols")
            if any(not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 10 for symbol in symbols):
                fail(f"beat {index} diagram symbols must be short strings")
            connectors = {"→", "->", "=>", "←", "<-", "↔"}
            if any(symbol.strip() in connectors for symbol in symbols):
                fail(f"beat {index} diagram should contain nodes only; arrows are added automatically")
        elif kind == "comparison":
            if not isinstance(visual.get("left"), str) or not isinstance(visual.get("right"), str):
                fail(f"beat {index} comparison needs left and right")
        elif kind == "symbol":
            if not isinstance(visual.get("symbol"), str) or not visual["symbol"].strip():
                fail(f"beat {index} symbol visual needs symbol")
        elif kind == "text":
            value = visual.get("text")
            if not isinstance(value, str) or not value.strip():
                fail(f"beat {index} text visual needs text")
            if len(value.split()) > 3:
                fail(f"beat {index} text visual must be at most 3 words")

        if beat.get("sfx") is not None and beat.get("sfx") not in ALLOWED_SFX:
            fail(f"beat {index} has unsupported sfx")
        if beat.get("memeIntent") is not None:
            validate_meme_intent(beat["memeIntent"], index)
            meme_count += 1

    reconstructed = normalized_space(" ".join(str(beat["text"]) for beat in beats))
    if reconstructed != normalized_space(narration):
        fail("beat text must reproduce the narration exactly and in order")

    if meme_count > 4:
        fail("normal Shorts may contain at most four meme moments")

    if path.name == "current.json":
        validate_editorial(data)

    print(f"Validated {path} with {len(beats)} voice-first beats and {meme_count} meme intents")


if __name__ == "__main__":
    main()
