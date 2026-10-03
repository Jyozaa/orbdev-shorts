from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import edge_tts

PUBLIC_DIR = Path("public")
AUDIO_PATH = PUBLIC_DIR / "voice.mp3"
CAPTIONS_PATH = PUBLIC_DIR / "captions.json"
CAPTION_LEAD_MS = int(os.getenv("ORBDEV_CAPTION_LEAD_MS", "180"))


def audio_duration_seconds(path: Path) -> float:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    value = subprocess.check_output(command, text=True).strip()
    return float(value)


def approximate_words(text: str, duration_seconds: float) -> list[dict[str, object]]:
    words = re.findall(r"\S+", text)
    if not words:
        return []

    weights = [max(1, len(re.sub(r"[^A-Za-z0-9]", "", word))) for word in words]
    total = sum(weights)
    cursor = 0.0
    output: list[dict[str, object]] = []

    for word, weight in zip(words, weights):
        width = duration_seconds * (weight / total)
        output.append(
            {
                "text": word,
                "startMs": round(cursor * 1000),
                "endMs": round((cursor + width) * 1000),
            }
        )
        cursor += width

    return output


async def render_primary(text: str) -> list[dict[str, object]]:
    voice = os.getenv("ORBDEV_VOICE", "en-GB-RyanNeural")
    rate = os.getenv("ORBDEV_RATE", "+8%")
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    captions: list[dict[str, object]] = []

    with AUDIO_PATH.open("wb") as audio_file:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_ms = int(chunk["offset"] / 10_000)
                duration_ms = int(chunk["duration"] / 10_000)
                captions.append(
                    {
                        "text": chunk["text"],
                        "startMs": start_ms,
                        "endMs": start_ms + max(1, duration_ms),
                    }
                )

    return captions


def render_fallback(text: str) -> None:
    wav_path = PUBLIC_DIR / "voice-fallback.wav"
    subprocess.run(
        ["espeak-ng", "-s", "178", "-w", str(wav_path), text],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(wav_path),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "3",
            str(AUDIO_PATH),
        ],
        check=True,
    )
    wav_path.unlink(missing_ok=True)


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_narration.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    text = story["narration"].strip()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    captions: list[dict[str, object]] = []
    try:
        captions = await render_primary(text)
    except Exception as exc:
        print(f"Primary narration unavailable: {exc}")
        render_fallback(text)

    duration = audio_duration_seconds(AUDIO_PATH)
    if not captions:
        captions = approximate_words(text, duration)

    if CAPTION_LEAD_MS > 0:
        captions = [
            {
                **caption,
                "startMs": max(0, int(caption["startMs"]) - CAPTION_LEAD_MS),
                "endMs": max(1, int(caption["endMs"]) - CAPTION_LEAD_MS),
            }
            for caption in captions
        ]

    CAPTIONS_PATH.write_text(
        json.dumps({"durationSeconds": duration, "words": captions}, indent=2),
        encoding="utf-8",
    )
    print(f"Narration ready: {duration:.2f}s, {len(captions)} timed words")


if __name__ == "__main__":
    asyncio.run(main())
