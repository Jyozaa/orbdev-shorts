"""Deterministic local Chatterbox Turbo narration, with Nano-only fallback.

The same generated/approved speaker reference is used by both models.
No Edge/eSpeak voice downgrade is permitted in this voice chain.
Heavy dependencies load lazily so lightweight regression tests need no models.
"""
from __future__ import annotations

import gc
import os
import re
import time
from pathlib import Path
from typing import Any

REFERENCE_SCRIPT = (
    "This is Orbdev. We break down complicated technology without making it "
    "complicated. A model can be enormous, and still use only a small part of "
    "itself at a time. That's the interesting bit. Now let's see how it works."
)
DEFAULT_REFERENCE = Path("build/chatterbox-voice-reference.wav")
DEFAULT_OUTPUT = Path("public/voice-chatterbox.wav")


def sentence_units(text: str) -> list[str]:
    """Preserve punctuation and decimal points while splitting natural pauses."""
    value = str(text).strip()
    if not value:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", value) if part.strip()]


def plan_chatterbox_chunks(text: str, target: int = 32, maximum: int = 65) -> list[str]:
    """Group complete sentences; avoid breaking jokes and technical names mid-word."""
    units = sentence_units(text)
    if not units:
        return []
    result: list[str] = []
    current: list[str] = []
    count = 0
    for unit in units:
        n = len(unit.split())
        if current and (count + n > maximum or (count >= target and n >= 5)):
            result.append(" ".join(current))
            current = []
            count = 0
        current.append(unit)
        count += n
    if current:
        result.append(" ".join(current))
    # Important: never lose or rewrite the user's narration.
    if " ".join(result) != " ".join(units):
        raise RuntimeError("Chatterbox sentence segmentation changed the narration")
    return result


def validate_waveform(audio: Any, sample_rate: int, word_count: int):
    import numpy as np

    wav = audio.detach().cpu().numpy() if hasattr(audio, "detach") else audio
    wav = np.asarray(wav, dtype=np.float32).squeeze()
    if wav.ndim != 1 or not np.isfinite(wav).all() or len(wav) < sample_rate // 2:
        raise RuntimeError("Chatterbox produced empty, damaged or non-finite audio")
    duration = len(wav) / sample_rate
    # Catch model hallucinations/truncation instead of publishing incomplete speech.
    if word_count >= 5 and not (word_count / 5.6 <= duration <= word_count / 1.1 + 7):
        raise RuntimeError(
            f"Implausible Chatterbox duration: {duration:.1f}s for {word_count} words"
        )
    if float(np.sqrt(np.mean(wav ** 2))) < 0.0001:
        raise RuntimeError("Chatterbox waveform is effectively silent")
    return wav


def trim_outer_silence(wav, sr: int, threshold: float = 0.002):
    import numpy as np

    active = np.flatnonzero(abs(wav) >= threshold)
    if active.size < sr // 10:
        return wav
    # Leave onset and release padding so neither first/last consonants clip.
    start = max(0, int(active[0]) - int(sr * 0.025))
    end = min(wav.size, int(active[-1]) + int(sr * 0.115) + 1)
    return wav[start:end]


def make_voice_reference(
    path: Path,
    voice: str = "am_michael",
    *,
    pipeline: Any | None = None,
) -> Path:
    """Generate a stable *synthetic* voice reference, never clone someone else.

    An optional user-owned/consented WAV can be supplied with
    ORBDEV_CHATTERBOX_REFERENCE_WAV. No user reference is stored in GitHub.
    """
    import numpy as np
    import soundfile as sf

    external = os.getenv("ORBDEV_CHATTERBOX_REFERENCE_WAV", "").strip()
    if external:
        source = Path(external)
        if not source.is_file():
            raise RuntimeError("Configured Chatterbox reference WAV is missing")
        data, sr = sf.read(source, dtype="float32", always_2d=False)
        if np.asarray(data).ndim > 2 or len(data) / sr < 6.0:
            raise RuntimeError("Voice reference must contain >=6 seconds of audio")
        return source
    if path.is_file():
        data, sr = sf.read(path, dtype="float32", always_2d=False)
        if len(data) / sr >= 6.0:
            return path

    if pipeline is None:
        from kokoro import KPipeline

        pipeline = KPipeline(lang_code="b" if voice.startswith("b") else "a")
    chunks = []
    for result in pipeline(REFERENCE_SCRIPT, voice=voice, speed=1.34):
        wav = result[2] if isinstance(result, tuple) else getattr(result, "audio", None)
        if wav is not None:
            part = np.asarray(wav, dtype=np.float32).reshape(-1)
            if len(part):
                chunks.append(part)
    if not chunks:
        raise RuntimeError("Unable to generate synthetic Chatterbox voice reference")
    audio = np.concatenate(chunks)
    if len(audio) / 24000 < 6:
        raise RuntimeError("Synthetic voice reference shorter than six seconds")
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(path, audio[: 24000 * 15], 24000, subtype="PCM_16")
    return path


def render_one(
    model: Any,
    speech_chunks: list[str],
    reference_path: Path,
    *,
    temperature: float,
    repetition_penalty: float,
    silence_ms: int,
    min_generated_wpm: float = 65,
) -> tuple[list[dict[str, object]], list[dict[str, object]], Any, int]:
    """Render a full video atomically; callers discard output on any failure."""
    import numpy as np

    from generate_narration import weighted_word_timings

    model.prepare_conditionals(str(reference_path))
    sr = int(model.sr)
    cursor = 0.0
    parts = []
    captions = []
    chunk_report: list[dict[str, object]] = []
    for index, text in enumerate(speech_chunks):
        t0 = time.perf_counter()
        wave = model.generate(
            text,
            temperature=temperature,
            repetition_penalty=repetition_penalty,
        )
        wav = trim_outer_silence(
            validate_waveform(wave, sr, len(text.split())), sr
        )
        seconds = wav.size / sr
        if (len(text.split()) / seconds * 60) < min_generated_wpm:
            raise RuntimeError(f"Chatterbox chunk {index} has unnaturally slow speech")
        start = cursor
        parts.append(wav)
        captions.extend(weighted_word_timings(text, start, seconds))
        cursor += seconds
        if index < len(speech_chunks) - 1 and silence_ms > 0:
            silence = np.zeros(round(sr * silence_ms / 1000), dtype=np.float32)
            parts.append(silence)
            cursor += silence.size / sr
        chunk_report.append({
            "text": text,
            "index": index,
            "startSeconds": round(start, 3),
            "endSeconds": round(cursor, 3),
            "generationSeconds": round(time.perf_counter() - t0, 2),
        })
    if not parts:
        raise RuntimeError("Chatterbox returned no waveform")
    return captions, chunk_report, np.concatenate(parts), sr


def render_chatterbox_with_fallback(
    story: dict[str, object],
    profile: dict[str, Any],
    output: Path = DEFAULT_OUTPUT,
    reference: Path = DEFAULT_REFERENCE,
    *,
    loader: Any | None = None,
    reference_factory: Any | None = None,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, Any]]:
    """Turbo first, Nano second; never Edge, eSpeak, or silent Kokoro fallback."""
    import soundfile as sf

    text = str(story.get("narration", "")).strip()
    speech_chunks = plan_chatterbox_chunks(
        text,
        target=int(profile.get("chunkTargetWords", 32)),
        maximum=int(profile.get("chunkMaxWords", 65)),
    )
    if not speech_chunks:
        raise RuntimeError("Story has no narration")
    reference_factory = reference_factory or make_voice_reference
    ref_path = reference_factory(reference, str(profile.get("voice", "am_michael")))
    if loader is None:
        from chatterbox.tts_turbo import ChatterboxTurboTTS

        loader = ChatterboxTurboTTS.from_pretrained
    device = os.getenv("ORBDEV_CHATTERBOX_DEVICE", "cpu").strip() or "cpu"
    temperature = float(profile.get("temperature", 0.75))
    repetition_penalty = float(profile.get("repetitionPenalty", 1.22))
    silence_ms = int(profile.get("chunkPauseMs", 65))
    failures: list[dict[str, str]] = []
    output.unlink(missing_ok=True)
    for engine, nano in [("chatterbox-turbo", False), ("chatterbox-nano", True)]:
        model = None
        t0 = time.perf_counter()
        try:
            model = loader(device=device, nano=nano)
            captions, chunk_report, audio, sr = render_one(
                model,
                speech_chunks,
                ref_path,
                temperature=temperature,
                repetition_penalty=repetition_penalty,
                silence_ms=silence_ms,
            )
            output.parent.mkdir(parents=True, exist_ok=True)
            sf.write(output, audio, sr, subtype="PCM_16")
            return captions, chunk_report, {
                "engine": engine,
                "usedFallback": nano,
                "referencePath": str(ref_path),
                "voice": str(profile.get("voice", "am_michael")),
                "device": device,
                "inferenceSeconds": round(time.perf_counter() - t0, 2),
                "fallbackFailures": failures,
                "chunkCount": len(speech_chunks),
            }
        except Exception as exc:
            failures.append({"engine": engine, "error": str(exc)})
            print(f"::warning::{engine} failed: {exc}", flush=True)
            output.unlink(missing_ok=True)
        finally:
            if model is not None:
                del model
            gc.collect()
    raise RuntimeError(
        "Both Chatterbox Turbo and Nano failed; refusing to use Edge, "
        "eSpeak or Kokoro for this video. Errors: " + str(failures)
    )
