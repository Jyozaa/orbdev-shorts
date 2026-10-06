"""Two different videos may discuss the same event. Only identical content is a duplicate.

Source URLs, titles, company names, and broad topic keys describe *subject*,
not video identity. Storyboard hashes are a cheap pre-render proxy; final MP4
SHA-256 is the authoritative post-render identity.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


def _canonical_text(value: object) -> str:
    return " ".join(str(value or "").split())


def story_plan_sha256(story: dict) -> str:
    """Fingerprint spoken script + visual/audio/meme planning, ignoring metadata.

    Does not require an LLM, network access, or API key. Identical editorial
    packaging under different filenames produces the same fingerprint.
    """
    if not isinstance(story, dict):
        return ""
    beats = story.get("beats")
    if not isinstance(beats, list) or not beats:
        return ""
    payload = {
        "narration": _canonical_text(story.get("narration")),
        "beats": [
            {
                "text": _canonical_text(beat.get("text")),
                "visual": beat.get("visual"),
                "sfx": beat.get("sfx"),
                "memeIntent": beat.get("memeIntent"),
                "editorialRole": beat.get("editorialRole"),
                "callbackKey": beat.get("callbackKey"),
            }
            for beat in beats if isinstance(beat, dict)
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_sha256(path: str | Path) -> str:
    """Hash the actual rendered bytes, not the story/event metadata."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def same_video(a: dict, b: dict) -> bool:
    """Prioritize matching MP4 hashes, otherwise compare complete story plans.

    Older history entries often lack fingerprints; matching topics alone
    cannot establish identical media and must not suppress new creative takes.
    """
    if not isinstance(a, dict) or not isinstance(b, dict):
        return False
    ha, hb = a.get("videoSha256"), b.get("videoSha256")
    if ha and hb:
        return str(ha).lower() == str(hb).lower()
    pa = a.get("storyPlanSha256") or story_plan_sha256(a)
    pb = b.get("storyPlanSha256") or story_plan_sha256(b)
    return bool(pa and pb and str(pa).lower() == str(pb).lower())


def duplicate(a: dict, b: dict) -> bool:
    """Backwards-compatible name: dedupe videos, never topics."""
    return same_video(a, b)


def same_video_file(path: str | Path, previous: list[dict]) -> dict | None:
    """Return receipt whose successfully uploaded MP4 is byte-for-byte equal."""
    digest = file_sha256(path)
    return next((row for row in previous
                 if row.get("youtubeVideoId") and
                 str(row.get("videoSha256") or "").lower() == digest), None)
