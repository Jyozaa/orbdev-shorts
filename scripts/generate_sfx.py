from __future__ import annotations

import asyncio
import math
import struct
import subprocess
import wave
from pathlib import Path

import edge_tts

SAMPLE_RATE = 44100
OUT = Path("public/sfx")


def write_wav(path: Path, samples: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        frames = bytearray()
        for sample in samples:
            value = max(-1.0, min(1.0, sample))
            frames.extend(struct.pack("<h", int(value * 32767)))
        handle.writeframes(frames)


def sweep(duration: float, start_hz: float, end_hz: float, gain: float) -> list[float]:
    count = int(duration * SAMPLE_RATE)
    out: list[float] = []
    phase = 0.0
    for index in range(count):
        p = index / max(1, count - 1)
        frequency = start_hz + (end_hz - start_hz) * p
        phase += 2 * math.pi * frequency / SAMPLE_RATE
        envelope = math.sin(math.pi * p) ** 1.5
        out.append(math.sin(phase) * envelope * gain)
    return out


def impact() -> list[float]:
    duration = 0.42
    count = int(duration * SAMPLE_RATE)
    out: list[float] = []
    for index in range(count):
        p = index / max(1, count - 1)
        env = math.exp(-7.2 * p)
        low = math.sin(2 * math.pi * 72 * index / SAMPLE_RATE)
        snap = math.sin(2 * math.pi * 720 * index / SAMPLE_RATE) * math.exp(-22 * p)
        out.append((low * 0.34 + snap * 0.16) * env)
    return out


def scratch() -> list[float]:
    duration = 0.48
    count = int(duration * SAMPLE_RATE)
    out: list[float] = []
    for index in range(count):
        p = index / max(1, count - 1)
        freq = 1450 - 1100 * p
        carrier = math.sin(2 * math.pi * freq * index / SAMPLE_RATE)
        gate = 1 if (index // 90) % 2 == 0 else -0.6
        env = (1 - p) ** 1.4
        out.append(carrier * gate * env * 0.16)
    return out


def tick() -> list[float]:
    duration = 0.10
    count = int(duration * SAMPLE_RATE)
    out: list[float] = []
    for index in range(count):
        p = index / max(1, count - 1)
        env = math.exp(-20 * p)
        signal = math.sin(2 * math.pi * 1600 * index / SAMPLE_RATE)
        out.append(signal * env * 0.22)
    return out


async def voice_reaction(path: Path, text: str, voice: str, rate: str, pitch: str) -> None:
    temp = path.with_suffix(".raw.mp3")
    try:
        communicator = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
            pitch=pitch,
            volume="+0%"
        )
        await communicator.save(str(temp))
        subprocess.run(
            [
                "ffmpeg","-y","-loglevel","error",
                "-i",str(temp),
                "-af","volume=1.55,acompressor=threshold=-18dB:ratio=3:attack=5:release=80",
                str(path)
            ],
            check=True
        )
    except Exception:
        fallback = path.with_suffix(".wav")
        subprocess.run(
            ["espeak-ng","-s","210","-w",str(fallback),text],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        subprocess.run(
            ["ffmpeg","-y","-loglevel","error","-i",str(fallback),"-af","volume=1.6",str(path)],
            check=True
        )
        fallback.unlink(missing_ok=True)
    finally:
        temp.unlink(missing_ok=True)


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    write_wav(OUT / "whoosh.wav", sweep(0.34, 220, 1300, 0.19))
    write_wav(OUT / "impact.wav", impact())
    write_wav(OUT / "scratch.wav", scratch())
    write_wav(OUT / "tick.wav", tick())

    await asyncio.gather(
        voice_reaction(OUT / "yay.mp3", "Yaaay!", "en-US-JennyNeural", "+18%", "+18Hz"),
        voice_reaction(OUT / "rage.mp3", "Nooooo! Aaaagh!", "en-US-GuyNeural", "+12%", "-12Hz")
    )


if __name__ == "__main__":
    asyncio.run(main())
