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
RAW_AUDIO_PATH = PUBLIC_DIR / "voice-raw.mp3"
AUDIO_PATH = PUBLIC_DIR / "voice.mp3"
CAPTIONS_PATH = PUBLIC_DIR / "captions.json"
CAPTION_LEAD_MS = int(os.getenv("ORBDEV_CAPTION_LEAD_MS", "80"))


def audio_duration_seconds(path: Path) -> float:
    value = subprocess.check_output(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(path)
        ],
        text=True,
    ).strip()
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
        output.append({
            "text": word,
            "startMs": round(cursor * 1000),
            "endMs": round((cursor + width) * 1000),
        })
        cursor += width
    return output


async def render_with_voice(text: str, voice: str) -> list[dict[str, object]]:
    rate = os.getenv("ORBDEV_RATE", "+8%")
    pitch = os.getenv("ORBDEV_PITCH", "+0Hz")
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch,
    )
    captions: list[dict[str, object]] = []
    RAW_AUDIO_PATH.unlink(missing_ok=True)

    with RAW_AUDIO_PATH.open("wb") as audio_file:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start_ms = int(chunk["offset"] / 10_000)
                duration_ms = int(chunk["duration"] / 10_000)
                captions.append({
                    "text": chunk["text"],
                    "startMs": start_ms,
                    "endMs": start_ms + max(1, duration_ms),
                })

    return captions


def process_voice(source: Path) -> None:
    # Preserve the neural voice's natural dynamics. Previous heavier compression
    # and pitch shifting made speech noticeably more synthetic.
    filters = ",".join([
        "highpass=f=58",
        "lowpass=f=16500",
        "equalizer=f=180:t=q:w=1.0:g=0.4",
        "equalizer=f=3200:t=q:w=1.2:g=0.6",
        "acompressor=threshold=-18dB:ratio=1.55:attack=12:release=180:makeup=1.0dB",
        "alimiter=limit=0.96:attack=5:release=70",
        "loudnorm=I=-15.5:TP=-1.5:LRA=7",
    ])
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
            "-af", filters, "-codec:a", "libmp3lame", "-q:a", "2", str(AUDIO_PATH)
        ],
        check=True,
    )


def render_fallback(text: str) -> None:
    wav_path = PUBLIC_DIR / "voice-fallback.wav"
    subprocess.run(
        ["espeak-ng", "-s", "195", "-w", str(wav_path), text],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process_voice(wav_path)
    wav_path.unlink(missing_ok=True)


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_narration.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    text = story["narration"].strip()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    preferred = os.getenv("ORBDEV_VOICE", "en-US-BrianMultilingualNeural")
    fallback_voice = os.getenv("ORBDEV_VOICE_FALLBACK", "en-US-AndrewMultilingualNeural")
    tertiary_voice = os.getenv("ORBDEV_VOICE_TERTIARY", "en-US-AndrewNeural")
    captions: list[dict[str, object]] = []

    ordered_voices = []
    for voice in (preferred, fallback_voice, tertiary_voice):
        if voice and voice not in ordered_voices:
            ordered_voices.append(voice)

    for voice in ordered_voices:
        try:
            captions = await render_with_voice(text, voice)
            process_voice(RAW_AUDIO_PATH)
            print(f"Narration voice: {voice}")
            break
        except Exception as exc:
            print(f"Voice unavailable ({voice}): {exc}")
            captions = []

    if not AUDIO_PATH.exists():
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
    RAW_AUDIO_PATH.unlink(missing_ok=True)
    print(f"Narration ready: {duration:.2f}s, {len(captions)} timed words")


if __name__ == "__main__":
    asyncio.run(main())
