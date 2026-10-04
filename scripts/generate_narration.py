from __future__ import annotations

import asyncio
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import edge_tts

PUBLIC_DIR = Path("public")
BUILD_DIR = Path("build")
RAW_AUDIO_PATH = PUBLIC_DIR / "voice-raw.mp3"
RAW_WAV_PATH = PUBLIC_DIR / "voice-kokoro.wav"
AUDIO_PATH = PUBLIC_DIR / "voice.mp3"
CAPTIONS_PATH = PUBLIC_DIR / "captions.json"
REPORT_PATH = BUILD_DIR / "narration-report.json"
PROFILE_PATH = Path("editorial/narration-profiles.json")

HARD_BREAK_ROLES = {"joke", "reaction", "punchline", "callback"}
ROLE_PRIORITY = ["punchline", "reaction", "joke", "callback", "analogy", "explanation", "setup", "transition", "fact"]


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


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
    out: list[dict[str, object]] = []
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


def load_profile() -> tuple[str, dict[str, Any]]:
    raw = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    name = os.getenv("ORBDEV_NARRATION_PROFILE", "").strip() or str(raw.get("defaultProfile") or "orbdev-dry")
    profiles = raw.get("profiles") or {}
    if name not in profiles:
        raise RuntimeError(f"unknown narration profile: {name}")
    profile = dict(profiles[name])

    if os.getenv("ORBDEV_KOKORO_VOICE", "").strip():
        profile["voice"] = os.getenv("ORBDEV_KOKORO_VOICE", "").strip()
        profile["langCode"] = "b" if profile["voice"].startswith("b") else "a"
    if os.getenv("ORBDEV_KOKORO_SPEED", "").strip():
        profile["baseSpeed"] = float(os.getenv("ORBDEV_KOKORO_SPEED", "1.18"))
    if os.getenv("ORBDEV_TARGET_WPM", "").strip():
        profile["targetWpm"] = float(os.getenv("ORBDEV_TARGET_WPM", "188"))
    if os.getenv("ORBDEV_SENTENCE_PAUSE_MS", "").strip():
        profile["sentencePauseMs"] = int(os.getenv("ORBDEV_SENTENCE_PAUSE_MS", "18"))
    return name, profile


def trim_edge_silence(arr, sr: int, threshold: float):
    import numpy as np

    if arr.size == 0:
        return arr
    active = np.flatnonzero(np.abs(arr) >= threshold)
    if active.size == 0:
        return arr
    pad = max(1, int(sr * 0.010))
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
    if tempo <= 0 or abs(tempo - 1.0) < 0.0001:
        return captions
    return [
        {
            **caption,
            "startMs": round(float(caption["startMs"]) / tempo),
            "endMs": round(float(caption["endMs"]) / tempo),
        }
        for caption in captions
    ]


def chunk_role(roles: list[str]) -> str:
    role_set = {str(role or "fact").lower() for role in roles}
    for role in ROLE_PRIORITY:
        if role in role_set:
            return role
    return "fact"


def ends_sentence(text: str) -> bool:
    return bool(re.search(r"[.!?][\"')\]]?$", text.strip()))


def ends_clause(text: str) -> bool:
    return bool(re.search(r"[,;:—-][\"')\]]?$", text.strip()))


def plan_speech_chunks(story: dict[str, object], profile: dict[str, Any]) -> list[dict[str, Any]]:
    beats = story.get("beats") if isinstance(story.get("beats"), list) else []
    if not beats:
        beats = [{"text": str(story.get("narration", "")), "editorialRole": "fact"}]

    target = int(profile.get("chunkTargetWords", 11))
    maximum = int(profile.get("chunkMaxWords", 16))
    minimum = int(profile.get("chunkMinWords", 5))
    chunks: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []

    def word_count(items: list[dict[str, Any]]) -> int:
        return sum(len(re.findall(r"\S+", str(item.get("text", "")))) for item in items)

    def flush() -> None:
        nonlocal current
        if not current:
            return
        text = " ".join(str(item.get("text", "")).strip() for item in current if str(item.get("text", "")).strip()).strip()
        if text:
            roles = [str(item.get("editorialRole", "fact")).lower() for item in current]
            chunks.append(
                {
                    "text": text,
                    "role": chunk_role(roles),
                    "roles": roles,
                    "beatCount": len(current),
                    "wordCount": len(re.findall(r"\S+", text)),
                }
            )
        current = []

    for beat in beats:
        if not isinstance(beat, dict):
            continue
        text = str(beat.get("text", "")).strip()
        if not text:
            continue
        role = str(beat.get("editorialRole", "fact")).lower()
        beat_words = len(re.findall(r"\S+", text))
        current_words = word_count(current)
        previous = current[-1] if current else None
        previous_role = str(previous.get("editorialRole", "fact")).lower() if previous else ""

        hard_boundary_before = bool(current) and (role in HARD_BREAK_ROLES or previous_role in HARD_BREAK_ROLES)
        size_boundary = bool(current) and current_words + beat_words > maximum
        semantic_boundary = bool(current) and current_words >= target and previous is not None and (
            ends_sentence(str(previous.get("text", ""))) or ends_clause(str(previous.get("text", "")))
        )

        if hard_boundary_before or size_boundary or semantic_boundary:
            flush()

        current.append(beat)
        total = word_count(current)

        if role in HARD_BREAK_ROLES:
            flush()
        elif ends_sentence(text) and total >= minimum:
            flush()
        elif total >= maximum:
            flush()

    flush()

    # Avoid tiny non-comedic fragments when they can be merged without exceeding the cap.
    merged: list[dict[str, Any]] = []
    for chunk in chunks:
        if (
            merged
            and chunk["wordCount"] < minimum
            and chunk["role"] not in HARD_BREAK_ROLES
            and merged[-1]["role"] not in HARD_BREAK_ROLES
            and merged[-1]["wordCount"] + chunk["wordCount"] <= maximum
        ):
            previous = merged[-1]
            previous["text"] = previous["text"] + " " + chunk["text"]
            previous["roles"] = previous["roles"] + chunk["roles"]
            previous["beatCount"] += chunk["beatCount"]
            previous["wordCount"] += chunk["wordCount"]
            previous["role"] = chunk_role(previous["roles"])
        else:
            merged.append(chunk)

    return merged


def role_profile(profile: dict[str, Any], role: str) -> dict[str, float]:
    roles = profile.get("roles") or {}
    raw = roles.get(role) or roles.get("fact") or {"speed": 1.0, "preMs": 0, "postMs": 4}
    return {
        "speed": float(raw.get("speed", 1.0)),
        "preMs": float(raw.get("preMs", 0)),
        "postMs": float(raw.get("postMs", 4)),
    }


def render_kokoro(
    story: dict[str, object],
    profile: dict[str, Any],
    base_speed: float,
    pipeline: Any | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, Any]]]:
    import numpy as np
    import soundfile as sf
    from kokoro import KPipeline

    voice = str(profile.get("voice") or "am_michael")
    lang_code = str(profile.get("langCode") or ("b" if voice.startswith("b") else "a"))
    if pipeline is None:
        pipeline = KPipeline(lang_code=lang_code)
    speech_chunks = plan_speech_chunks(story, profile)

    chunks = []
    captions: list[dict[str, object]] = []
    chunk_report: list[dict[str, Any]] = []
    cursor = 0.0
    sr = 24000
    silence_threshold = float(profile.get("silenceThreshold", 0.0035))
    sentence_pause_ms = int(profile.get("sentencePauseMs", 18))

    for index, chunk in enumerate(speech_chunks):
        role = str(chunk["role"])
        rp = role_profile(profile, role)
        pre_ms = int(rp["preMs"])
        post_ms = int(rp["postMs"])
        chunk_text = str(chunk["text"])
        cursor = add_pause(chunks, cursor, pre_ms, sr)
        start = cursor
        local_speed = base_speed * float(rp["speed"])

        for result in pipeline(chunk_text, voice=voice, speed=local_speed):
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
            arr = trim_edge_silence(arr, sr, silence_threshold)
            spoken = str(graphemes).strip()
            duration = arr.size / sr
            if spoken:
                captions.extend(weighted_word_timings(spoken, cursor, duration))
            chunks.append(arr)
            cursor += duration

        if ends_sentence(chunk_text):
            post_ms = max(post_ms, sentence_pause_ms)
        cursor = add_pause(chunks, cursor, post_ms, sr)
        chunk_report.append(
            {
                **chunk,
                "index": index,
                "speed": round(local_speed, 4),
                "preMs": pre_ms,
                "postMs": post_ms,
                "startSeconds": round(start, 3),
                "endSeconds": round(cursor, 3),
            }
        )

    if not chunks:
        raise RuntimeError("Kokoro produced no audio")

    sf.write(RAW_WAV_PATH, np.concatenate(chunks), sr)
    return captions, chunk_report


async def render_edge(text: str, voice: str, rate: str) -> list[dict[str, object]]:
    communicator = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch="+0Hz")
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
                    {"text": chunk["text"], "startMs": start, "endMs": start + max(1, duration)}
                )
    return captions


def choose_post_tempo(raw_wpm: float, profile: dict[str, Any]) -> float:
    target = float(profile.get("targetWpm", 188))
    lo = float(profile.get("postTempoMin", 0.985))
    hi = float(profile.get("postTempoMax", 1.025))
    if raw_wpm <= 0:
        return 1.0
    tempo = clamp(target / raw_wpm, lo, hi)
    if abs(tempo - 1.0) < 0.004:
        return 1.0
    return tempo


def process_voice(source: Path, tempo: float) -> None:
    filters = []
    if abs(tempo - 1.0) >= 0.0001:
        filters.append(f"atempo={tempo:.5f}")
    filters.extend(
        [
            "highpass=f=58",
            "equalizer=f=220:t=q:w=1.0:g=-0.7",
            "equalizer=f=3200:t=q:w=1.1:g=0.8",
            "acompressor=threshold=-15dB:ratio=1.22:attack=18:release=210:makeup=0.3dB",
            "alimiter=limit=0.97:attack=5:release=80",
            "loudnorm=I=-16:TP=-1.5:LRA=8",
        ]
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
            ",".join(filters),
            "-codec:a",
            "libmp3lame",
            "-q:a",
            "2",
            str(AUDIO_PATH),
        ],
        check=True,
    )


def render_espeak(text: str, tempo: float) -> None:
    wav = PUBLIC_DIR / "voice-fallback.wav"
    subprocess.run(
        ["espeak-ng", "-s", "190", "-w", str(wav), text],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    process_voice(wav, tempo)
    wav.unlink(missing_ok=True)


def native_retarget_speed(base_speed: float, raw_wpm: float, profile: dict[str, Any]) -> float:
    target = float(profile.get("targetWpm", 188))
    tolerance = float(profile.get("nativeRetargetToleranceWpm", 6))
    if raw_wpm <= 0 or abs(raw_wpm - target) <= tolerance:
        return base_speed
    multiplier = clamp(
        target / raw_wpm,
        float(profile.get("nativeRetargetMinMultiplier", 0.94)),
        float(profile.get("nativeRetargetMaxMultiplier", 1.07)),
    )
    adjusted = base_speed * multiplier
    return adjusted if abs(adjusted - base_speed) >= 0.008 else base_speed


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: generate_narration.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    text = str(story["narration"]).strip()
    word_count = len(re.findall(r"\S+", text))
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_PATH.unlink(missing_ok=True)
    captions: list[dict[str, object]] = []
    profile_name, profile = load_profile()
    base_speed = float(profile.get("baseSpeed", 1.18))
    engine = "kokoro"
    chunk_report: list[dict[str, Any]] = []
    native_passes = 0
    raw_duration = 0.0
    raw_wpm = 0.0

    try:
        from kokoro import KPipeline

        voice = str(profile.get("voice") or "am_michael")
        lang_code = str(profile.get("langCode") or ("b" if voice.startswith("b") else "a"))
        kokoro_pipeline = KPipeline(lang_code=lang_code)
        captions, chunk_report = render_kokoro(story, profile, base_speed, kokoro_pipeline)
        native_passes = 1
        raw_duration = audio_duration_seconds(RAW_WAV_PATH)
        raw_wpm = (word_count / max(raw_duration, 0.01)) * 60
        adjusted_speed = native_retarget_speed(base_speed, raw_wpm, profile)
        if abs(adjusted_speed - base_speed) >= 0.008:
            print(
                f"Native cadence retarget: {raw_wpm:.0f} WPM -> target "
                f"{float(profile.get('targetWpm', 188)):.0f}; base speed "
                f"{base_speed:.3f}x -> {adjusted_speed:.3f}x"
            )
            base_speed = adjusted_speed
            captions, chunk_report = render_kokoro(story, profile, base_speed, kokoro_pipeline)
            native_passes = 2
            raw_duration = audio_duration_seconds(RAW_WAV_PATH)
            raw_wpm = (word_count / max(raw_duration, 0.01)) * 60

        tempo = choose_post_tempo(raw_wpm, profile)
        process_voice(RAW_WAV_PATH, tempo)
        captions = scale_timings(captions, tempo)
        print(
            f"Narration engine: Kokoro-82M / {profile.get('voice')} / profile={profile_name}; "
            f"{len(chunk_report)} speech chunks; native={base_speed:.3f}x; post-tempo={tempo:.3f}x"
        )
    except Exception as exc:
        print(f"Kokoro unavailable: {exc}")
        engine = "edge"
        tempo = 1.0
        for voice in (
            os.getenv("ORBDEV_VOICE_FALLBACK", "en-US-BrianMultilingualNeural"),
            os.getenv("ORBDEV_VOICE_TERTIARY", "en-US-AndrewMultilingualNeural"),
        ):
            try:
                captions = await render_edge(text, voice, str(profile.get("edgeRate", "+10%")))
                raw_duration = audio_duration_seconds(RAW_AUDIO_PATH)
                raw_wpm = (word_count / max(raw_duration, 0.01)) * 60
                tempo = choose_post_tempo(raw_wpm, profile)
                process_voice(RAW_AUDIO_PATH, tempo)
                captions = scale_timings(captions, tempo)
                print(f"Narration engine fallback: Edge / {voice}; post-tempo={tempo:.3f}x")
                break
            except Exception as edge_exc:
                print(f"Edge voice unavailable ({voice}): {edge_exc}")
                captions = []

    if not AUDIO_PATH.exists():
        engine = "espeak"
        tempo = 1.0
        render_espeak(text, tempo)

    duration = audio_duration_seconds(AUDIO_PATH)
    expected = word_count
    if not captions or abs(len(captions) - expected) > max(4, expected * 0.08):
        captions = weighted_word_timings(text, 0, duration)

    lead_ms = int(os.getenv("ORBDEV_CAPTION_LEAD_MS", "45"))
    if lead_ms > 0:
        captions = [
            {
                **caption,
                "startMs": max(0, int(caption["startMs"]) - lead_ms),
                "endMs": max(1, int(caption["endMs"]) - lead_ms),
            }
            for caption in captions
        ]

    CAPTIONS_PATH.write_text(
        json.dumps({"durationSeconds": duration, "words": captions}, indent=2),
        encoding="utf-8",
    )

    final_wpm = (word_count / max(duration, 0.01)) * 60
    report = {
        "profile": profile_name,
        "engine": engine,
        "voice": profile.get("voice"),
        "targetWpm": float(profile.get("targetWpm", 188)),
        "wordCount": word_count,
        "speechChunkCount": len(chunk_report),
        "nativePasses": native_passes,
        "nativeBaseSpeed": round(base_speed, 4),
        "rawDurationSeconds": round(raw_duration, 3),
        "rawWpm": round(raw_wpm, 1),
        "finalDurationSeconds": round(duration, 3),
        "finalWpm": round(final_wpm, 1),
        "postTempo": round(tempo, 4),
        "chunks": chunk_report,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if not 175 <= final_wpm <= 200:
        print(f"::warning::Narration cadence {final_wpm:.0f} WPM is outside the preferred 175-200 WPM band")

    RAW_AUDIO_PATH.unlink(missing_ok=True)
    RAW_WAV_PATH.unlink(missing_ok=True)
    print(
        f"Narration ready: {duration:.2f}s, {len(captions)} timed words, "
        f"{final_wpm:.0f} effective WPM"
    )


if __name__ == "__main__":
    asyncio.run(main())
