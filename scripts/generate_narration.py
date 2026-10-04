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
RAW_WAV_PATH = PUBLIC_DIR / "voice-kokoro.wav"
AUDIO_PATH = PUBLIC_DIR / "voice.mp3"
CAPTIONS_PATH = PUBLIC_DIR / "captions.json"

CAPTION_LEAD_MS = int(os.getenv("ORBDEV_CAPTION_LEAD_MS", "45"))
VOICE_TEMPO = float(os.getenv("ORBDEV_VOICE_TEMPO", "1.04"))
BASE_KOKORO_SPEED = float(os.getenv("ORBDEV_KOKORO_SPEED", "1.26"))
DEFAULT_SENTENCE_PAUSE_MS = int(os.getenv("ORBDEV_SENTENCE_PAUSE_MS", "18"))

ROLE_PROFILES = {
    "fact": {"speed": 1.03, "preMs": 0, "postMs": 8},
    "setup": {"speed": 1.04, "preMs": 0, "postMs": 8},
    "explanation": {"speed": 1.00, "preMs": 0, "postMs": 10},
    "analogy": {"speed": 0.98, "preMs": 14, "postMs": 14},
    "joke": {"speed": 0.97, "preMs": 22, "postMs": 18},
    "reaction": {"speed": 0.96, "preMs": 30, "postMs": 16},
    "punchline": {"speed": 0.94, "preMs": 52, "postMs": 24},
    "callback": {"speed": 0.97, "preMs": 24, "postMs": 18},
    "transition": {"speed": 1.05, "preMs": 0, "postMs": 6},
}


def audio_duration_seconds(path: Path) -> float:
    return float(
        subprocess.check_output(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(path),
            ],
            text=True,
        ).strip()
    )


def weighted_word_timings(text: str, start: float, duration: float) -> list[dict[str, object]]:
    words = re.findall(r"\S+", text)
    if not words:
        return []
    weights = [max(1, len(re.sub(r"[^A-Za-z0-9]", "", word))) for word in words]
    total = max(1, sum(weights))
    cursor = start
    out = []
    for word, weight in zip(words, weights):
        width = duration * (weight / total)
        out.append(
            {
                "text": word,
                "startMs": round(cursor * 1000),
                "endMs": round((cursor + width) * 1000),
            }
        )
        cursor += width
    return out


def trim_edge_silence(arr, sr: int):
    import numpy as np

    if arr.size == 0:
        return arr
    threshold = float(os.getenv("ORBDEV_SILENCE_THRESHOLD", "0.0035"))
    active = np.flatnonzero(np.abs(arr) >= threshold)
    if active.size == 0:
        return arr
    pad = max(1, int(sr * 0.012))
    start = max(0, int(active[0]) - pad)
    end = min(arr.size, int(active[-1]) + pad + 1)
    return arr[start:end]


def add_pause(chunks, cursor: float, milliseconds: int, sr: int) -> float:
    import numpy as np

    if milliseconds <= 0:
        return cursor
    pause = np.zeros(int(sr * (milliseconds / 1000.0)), dtype=np.float32)
    chunks.append(pause)
    return cursor + pause.size / sr


def scale_timings(captions: list[dict[str, object]], tempo: float) -> list[dict[str, object]]:
    if tempo <= 0:
        return captions
    return [
        {
            **caption,
            "startMs": round(float(caption["startMs"]) / tempo),
            "endMs": round(float(caption["endMs"]) / tempo),
        }
        for caption in captions
    ]


def role_profile(role: str | None) -> dict[str, float]:
    return ROLE_PROFILES.get(str(role or "").lower(), {"speed": 1.0, "preMs": 0, "postMs": 10})


def render_kokoro(story: dict[str, object]) -> list[dict[str, object]]:
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    voice = os.getenv("ORBDEV_KOKORO_VOICE", "am_michael")
    pipeline = KPipeline(lang_code="a")
    beats = story.get("beats") if isinstance(story.get("beats"), list) else []
    if not beats:
        beats = [{"text": str(story.get("narration", "")), "editorialRole": "fact"}]

    chunks = []
    captions: list[dict[str, object]] = []
    cursor = 0.0
    sr = 24000
    role_counts: dict[str, int] = {}

    for beat in beats:
        if not isinstance(beat, dict):
            continue
        beat_text = str(beat.get("text", "")).strip()
        if not beat_text:
            continue
        role = str(beat.get("editorialRole", "fact")).lower()
        profile = role_profile(role)
        role_counts[role] = role_counts.get(role, 0) + 1

        cursor = add_pause(chunks, cursor, int(profile["preMs"]), sr)
        local_speed = BASE_KOKORO_SPEED * float(profile["speed"])
        for result in pipeline(beat_text, voice=voice, speed=local_speed):
            try:
                graphemes, _phonemes, audio = result
            except Exception:
                graphemes = getattr(result, "graphemes", "")
                audio = getattr(result, "audio", getattr(result, "output", None))
            if audio is None:
                continue
            arr = np.asarray(audio, dtype=np.float32).reshape(-1)
            if arr.size == 0:
                continue
            arr = trim_edge_silence(arr, sr)
            spoken = str(graphemes).strip()
            duration = arr.size / sr
            if spoken:
                captions.extend(weighted_word_timings(spoken, cursor, duration))
            chunks.append(arr)
            cursor += duration

        post_ms = int(profile["postMs"])
        if beat_text.endswith((".", "!", "?")):
            post_ms = max(post_ms, DEFAULT_SENTENCE_PAUSE_MS)
        cursor = add_pause(chunks, cursor, post_ms, sr)

    if not chunks:
        raise RuntimeError("Kokoro produced no audio")

    sf.write(RAW_WAV_PATH, np.concatenate(chunks), sr)
    role_summary = ", ".join(f"{key}:{value}" for key, value in sorted(role_counts.items()))
    print(
        f"Narration engine: Kokoro-82M / {voice} @ {BASE_KOKORO_SPEED:.2f}x base, "
        f"role-aware ({role_summary})"
    )
    return captions


async def render_edge(text: str, voice: str) -> list[dict[str, object]]:
    communicator = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=os.getenv("ORBDEV_EDGE_RATE", "+12%"),
        pitch="+0Hz",
    )
    captions = []
    RAW_AUDIO_PATH.unlink(missing_ok=True)
    with RAW_AUDIO_PATH.open("wb") as output:
        async for chunk in communicator.stream():
            if chunk["type"] == "audio":
                output.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = int(chunk["offset"] / 10000)
                duration = int(chunk["duration"] / 10000)
                captions.append(
                    {
                        "text": chunk["text"],
                        "startMs": start,
                        "endMs": start + max(1, duration),
                    }
                )
    return captions


def process_voice(source: Path) -> None:
    filters = (
        f"atempo={VOICE_TEMPO:.4f},"
        "highpass=f=52,"
        "acompressor=threshold=-15dB:ratio=1.25:attack=18:release=220:makeup=0.4dB,"
        "alimiter=limit=0.97:attack=5:release=80,"
        "loudnorm=I=-16:TP=-1.5:LRA=9"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(source),
            "-af",
            filters,
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(AUDIO_PATH),
        ],
        check=True,
    )


def render_espeak(text: str) -> None:
    wav = PUBLIC_DIR / "voice-fallback.wav"
    subprocess.run(
        ["espeak-ng", "-s", "190", "-w", str(wav), text],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process_voice(wav)
    wav.unlink(missing_ok=True)


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_narration.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    text = str(story["narration"]).strip()
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_PATH.unlink(missing_ok=True)
    captions: list[dict[str, object]] = []

    try:
        captions = render_kokoro(story)
        process_voice(RAW_WAV_PATH)
        captions = scale_timings(captions, VOICE_TEMPO)
    except Exception as exc:
        print(f"Kokoro unavailable: {exc}")
        for voice in (
            os.getenv("ORBDEV_VOICE_FALLBACK", "en-US-BrianMultilingualNeural"),
            os.getenv("ORBDEV_VOICE_TERTIARY", "en-US-AndrewMultilingualNeural"),
        ):
            try:
                captions = await render_edge(text, voice)
                process_voice(RAW_AUDIO_PATH)
                captions = scale_timings(captions, VOICE_TEMPO)
                print(f"Narration engine fallback: Edge / {voice}")
                break
            except Exception as edge_exc:
                print(f"Edge voice unavailable ({voice}): {edge_exc}")
                captions = []

    if not AUDIO_PATH.exists():
        render_espeak(text)

    duration = audio_duration_seconds(AUDIO_PATH)
    expected = len(re.findall(r"\S+", text))
    if not captions or abs(len(captions) - expected) > max(4, expected * 0.08):
        captions = weighted_word_timings(text, 0, duration)

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

    word_count = len(re.findall(r"\S+", text))
    wpm = (word_count / max(duration, 0.01)) * 60
    RAW_AUDIO_PATH.unlink(missing_ok=True)
    RAW_WAV_PATH.unlink(missing_ok=True)
    print(
        f"Narration ready: {duration:.2f}s, {len(captions)} timed words, "
        f"{wpm:.0f} effective WPM"
    )


if __name__ == "__main__":
    asyncio.run(main())
