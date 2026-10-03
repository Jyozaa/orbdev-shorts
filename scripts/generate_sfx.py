from __future__ import annotations

import math
import struct
import wave
from pathlib import Path

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


def tone(duration: float, start_hz: float, end_hz: float, gain: float) -> list[float]:
    count = int(duration * SAMPLE_RATE)
    output: list[float] = []
    for index in range(count):
        t = index / SAMPLE_RATE
        p = index / max(1, count - 1)
        frequency = start_hz + (end_hz - start_hz) * p
        envelope = math.sin(math.pi * p) ** 1.7
        output.append(math.sin(2 * math.pi * frequency * t) * envelope * gain)
    return output


def click() -> list[float]:
    duration = 0.08
    count = int(duration * SAMPLE_RATE)
    output: list[float] = []
    for index in range(count):
        p = index / max(1, count - 1)
        envelope = math.exp(-18 * p)
        signal = (
            math.sin(2 * math.pi * 1200 * index / SAMPLE_RATE)
            + 0.45 * math.sin(2 * math.pi * 2300 * index / SAMPLE_RATE)
        )
        output.append(signal * envelope * 0.16)
    return output


def main() -> None:
    write_wav(OUT / "whoosh.wav", tone(0.24, 260, 920, 0.13))
    write_wav(OUT / "drop.wav", tone(0.18, 720, 180, 0.14))
    write_wav(OUT / "tick.wav", click())


if __name__ == "__main__":
    main()
