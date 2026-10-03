from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_VISUALS = {
    "source", "metric", "diagram", "comparison", "symbol", "text",
    "logo", "flow", "chart", "timeline", "network", "explain"
}
ALLOWED_SFX = {"scratch", "impact", "whoosh", "tick", "none"}
ALLOWED_PURPOSES = {"reaction", "punchline", "contrast", "confusion", "failure", "success", "waiting", "absurdity", "emphasis"}
ALLOWED_TONES = {"positive", "negative", "surprised", "confused", "awkward", "deadpan", "chaotic", "neutral"}
ALLOWED_MEDIA = {"audio", "image", "video", "any"}
ALLOWED_PRESENTATIONS = {"auto", "overlay", "cutaway"}
ALLOWED_FLOW_KINDS = {"logo", "symbol", "text"}


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
        if not isinstance(value, (int, float)) or value <= 0 or value > 3.5:
            fail(f"beat {beat_index} max meme duration must be between 0 and 3.5 seconds")


def validate_flow(nodes: object, beat_index: int) -> None:
    if not isinstance(nodes, list) or not 2 <= len(nodes) <= 4:
        fail(f"beat {beat_index} flow needs 2-4 nodes")
    for node_index, node in enumerate(nodes):
        if not isinstance(node, dict) or node.get("kind") not in ALLOWED_FLOW_KINDS:
            fail(f"beat {beat_index} flow node {node_index} has invalid kind")
        if node["kind"] == "logo":
            slug = node.get("slug")
            if not isinstance(slug, str) or not slug.strip():
                fail(f"beat {beat_index} flow logo node {node_index} needs slug")
        else:
            value = node.get("value")
            if not isinstance(value, str) or not value.strip() or len(value) > 12:
                fail(f"beat {beat_index} flow node {node_index} needs a short value")


def family(kind: str) -> str:
    if kind in {"source", "logo"}:
        return "brand-source"
    if kind in {"flow", "diagram", "network"}:
        return "diagram"
    if kind in {"chart", "metric"}:
        return "data"
    if kind in {"timeline"}:
        return "timeline"
    if kind in {"comparison"}:
        return "comparison"
    return "minimal"


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
    text_visual_count = 0
    rich_visual_count = 0
    visual_types: list[str] = []
    families: set[str] = set()

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
        kind = str(visual["type"])
        visual_types.append(kind)
        families.add(family(kind))

        if kind == "source":
            if not isinstance(visual.get("sourceIndex"), int) or visual["sourceIndex"] < 0:
                fail(f"beat {index} source visual needs sourceIndex")
            query = visual.get("query")
            if not isinstance(query, str) or len(query.strip()) < 3:
                fail(f"beat {index} source visual needs a semantic query")
            if visual.get("fit") is not None and visual.get("fit") not in {"contain", "cover"}:
                fail(f"beat {index} source fit must be contain or cover")
            annotations = visual.get("annotations", [])
            if annotations is not None:
                if not isinstance(annotations, list) or len(annotations) > 3:
                    fail(f"beat {index} source annotations must contain at most 3 items")
                for annotation in annotations:
                    if not isinstance(annotation, dict) or not isinstance(annotation.get("label"), str):
                        fail(f"beat {index} source annotations need labels")
                    if not isinstance(annotation.get("x"), (int, float)) or not 0 <= annotation["x"] <= 100:
                        fail(f"beat {index} source annotation x must be 0-100")
                    if not isinstance(annotation.get("y"), (int, float)) or not 0 <= annotation["y"] <= 100:
                        fail(f"beat {index} source annotation y must be 0-100")
            rich_visual_count += 1
        elif kind == "metric":
            if not isinstance(visual.get("value"), str) or not visual["value"].strip():
                fail(f"beat {index} metric needs value")
        elif kind == "diagram":
            symbols = visual.get("symbols")
            if not isinstance(symbols, list) or not 2 <= len(symbols) <= 4:
                fail(f"beat {index} diagram needs 2-4 symbols")
            if any(not isinstance(symbol, str) or not symbol.strip() or len(symbol) > 10 for symbol in symbols):
                fail(f"beat {index} diagram symbols must be short strings")
            rich_visual_count += 1
        elif kind == "comparison":
            if not isinstance(visual.get("left"), str) or not isinstance(visual.get("right"), str):
                fail(f"beat {index} comparison needs left and right")
            rich_visual_count += 1
        elif kind == "symbol":
            if not isinstance(visual.get("symbol"), str) or not visual["symbol"].strip():
                fail(f"beat {index} symbol visual needs symbol")
        elif kind == "text":
            value = visual.get("text")
            if not isinstance(value, str) or not value.strip():
                fail(f"beat {index} text visual needs text")
            if len(value.split()) > 3:
                fail(f"beat {index} text visual must be at most 3 words")
            text_visual_count += 1
        elif kind == "logo":
            slug = visual.get("slug")
            if not isinstance(slug, str) or not slug.strip():
                fail(f"beat {index} logo visual needs slug")
            rich_visual_count += 1
        elif kind == "flow":
            validate_flow(visual.get("nodes"), index)
            rich_visual_count += 1
        elif kind == "chart":
            bars = visual.get("bars")
            if not isinstance(bars, list) or not 2 <= len(bars) <= 5:
                fail(f"beat {index} chart needs 2-5 bars")
            for bar in bars:
                if not isinstance(bar, dict):
                    fail(f"beat {index} chart bars must be objects")
                if not isinstance(bar.get("label"), str) or not isinstance(bar.get("value"), str):
                    fail(f"beat {index} chart bars need label and value")
                amount = bar.get("amount")
                if not isinstance(amount, (int, float)) or not 0 <= amount <= 100:
                    fail(f"beat {index} chart amount must be 0-100")
            rich_visual_count += 1
        elif kind == "timeline":
            points = visual.get("points")
            if not isinstance(points, list) or not 2 <= len(points) <= 5:
                fail(f"beat {index} timeline needs 2-5 points")
            for point in points:
                if not isinstance(point, dict) or not isinstance(point.get("label"), str):
                    fail(f"beat {index} timeline points need labels")
                position = point.get("position")
                if not isinstance(position, (int, float)) or not 0 <= position <= 100:
                    fail(f"beat {index} timeline positions must be 0-100")
            rich_visual_count += 1
        elif kind == "network":
            center = visual.get("center")
            nodes = visual.get("nodes")
            if not isinstance(center, str) or not center.strip():
                fail(f"beat {index} network needs center")
            if not isinstance(nodes, list) or not 2 <= len(nodes) <= 6:
                fail(f"beat {index} network needs 2-6 nodes")
            if any(not isinstance(node, str) or not node.strip() or len(node) > 12 for node in nodes):
                fail(f"beat {index} network nodes must be short strings")
            rich_visual_count += 1
        elif kind == "explain":
            mode = visual.get("mode")
            if mode not in {"pixel-upscale","network-shrink","capacity","stability","pipeline","fanout"}:
                fail(f"beat {index} has invalid explain mode")
            if mode == "network-shrink":
                for key in ("fromLayers","toLayers"):
                    layers = visual.get(key)
                    if not isinstance(layers, list) or not 2 <= len(layers) <= 5 or any(not isinstance(v, int) or not 1 <= v <= 7 for v in layers):
                        fail(f"beat {index} {key} needs 2-5 layer sizes from 1-7")
            if mode == "capacity":
                load = visual.get("load")
                if not isinstance(load, (int,float)) or not 0 <= load <= 100:
                    fail(f"beat {index} capacity load must be 0-100")
            if mode == "pipeline":
                stages = visual.get("stages")
                if not isinstance(stages, list) or not 2 <= len(stages) <= 5:
                    fail(f"beat {index} pipeline needs 2-5 stages")
            if mode == "fanout":
                nodes = visual.get("nodes")
                if not isinstance(nodes, list) or not 2 <= len(nodes) <= 6:
                    fail(f"beat {index} fanout needs 2-6 nodes")
            rich_visual_count += 1

        if beat.get("sfx") is not None and beat.get("sfx") not in ALLOWED_SFX:
            fail(f"beat {index} has unsupported sfx")
        if beat.get("memeIntent") is not None:
            validate_meme_intent(beat["memeIntent"], index)
            meme_count += 1

    reconstructed = normalized_space(" ".join(str(beat["text"]) for beat in beats))
    if reconstructed != normalized_space(narration):
        fail("beat text must reproduce the narration exactly and in order")

    if meme_count > 4:
        fail("normal Shorts may contain at most four explicit meme moments")

    if text_visual_count > max(2, math.ceil(len(beats) * 0.25)):
        fail("too many text-only visuals; use logos, diagrams, networks, charts, timelines, source visuals or comparisons")

    if rich_visual_count < math.ceil(len(beats) * 0.55):
        fail("not enough rich visuals; at least 55 percent of beats must use rich graphical treatments")

    if len(families) < 4:
        fail("visual treatment is too repetitive; use at least four visual families in a normal Short")

    for index in range(len(visual_types) - 2):
        if visual_types[index] == visual_types[index + 1] == visual_types[index + 2]:
            fail(f"visual treatment repeats three times starting at beat {index}")

    generic_flow_count = sum(1 for kind in visual_types if kind in {"flow", "diagram"})
    if generic_flow_count > math.ceil(len(beats) * 0.35):
        fail("too many generic flow/diagram beats; use charts, timelines, networks, logos, source visuals or comparisons")

    if len(beats) >= 14 and visual_types.count("explain") < 2:
        fail("long technical Shorts need at least two explanatory animation beats")

    if path.name == "current.json":
        validate_editorial(data)

    print(
        f"Validated {path}: {len(beats)} beats, {meme_count} explicit memes, "
        f"{rich_visual_count} rich visuals, {len(families)} visual families"
    )


if __name__ == "__main__":
    main()
