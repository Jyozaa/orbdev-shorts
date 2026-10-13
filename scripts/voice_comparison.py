#!/usr/bin/env python3
"""One-off offline voice benchmark. Never changes the production narrator.

Uses the start of stories/current.json for an identical, fact-checked sample,
synthesizes the current Kokoro Michael baseline, then conditions Chatterbox
Nano and Turbo on the same 10+ second generated Kokoro reference.
"""
from __future__ import annotations

import gc
import json
import os
from pathlib import Path
import platform
import time
import traceback

import numpy as np
import soundfile as sf
import torch

OUT = Path("out/voice-comparison")
OUT.mkdir(parents=True, exist_ok=True)
STORY = Path("stories/current.json")
REPORT = OUT / "comparison-report.json"


def write_report(report: dict) -> None:
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def normalize_audio(audio) -> np.ndarray:
    if hasattr(audio, "detach"):
        audio = audio.detach().cpu().numpy()
    audio = np.asarray(audio, dtype=np.float32).squeeze()
    if audio.ndim != 1 or len(audio) < 1000:
        raise RuntimeError(f"unexpected TTS waveform shape {audio.shape}")
    if not np.all(np.isfinite(audio)):
        raise RuntimeError("non-finite TTS samples")
    # Normalize the three tracks to the same perceived broad loudness range.
    rms = float(np.sqrt(np.mean(audio * audio)))
    if rms > 0:
        audio = audio * min(2.0, (10 ** (-20 / 20)) / rms)
    peak = float(np.max(np.abs(audio)))
    if peak > 0.96:
        audio *= 0.96 / peak
    return audio


def save_audio(path: Path, samples, sr: int) -> float:
    audio = normalize_audio(samples)
    sf.write(str(path), audio, sr, subtype="PCM_16")
    return float(len(audio)) / sr


def main() -> None:
    torch.set_num_threads(4)
    story = json.loads(STORY.read_text(encoding="utf-8"))
    narration = story["narration"]
    text = narration.split("Context can reach", 1)[0].strip()
    assert 45 <= len(text.split()) <= 80, "Voice sample should be about 20-30 seconds"
    report = {
        "sourceStory": str(STORY),
        "slug": story["slug"],
        "text": text,
        "wordCount": len(text.split()),
        "voiceReference": "Generated 10+ seconds of the current Kokoro am_michael voice; no external speaker copied",
        "hardware": {"platform": platform.platform(), "torch": torch.__version__,
                     "cpuThreads": torch.get_num_threads(), "cuda": bool(torch.cuda.is_available())},
        "samples": {},
        "modelSwapPerformed": False,
    }
    (OUT / "comparison-script.txt").write_text(text + "\n", encoding="utf-8")
    write_report(report)

    # Same voice, original sample and speed as the production deadpan profile.
    from kokoro import KPipeline
    profile = json.loads(Path("editorial/narration-profiles.json").read_text(encoding="utf-8"))
    prod = profile["profiles"]["orbdev-deadpan"]
    reference_voice = prod["voice"]
    t0 = time.perf_counter()
    pipeline = KPipeline(lang_code=prod["langCode"])
    kokoro_parts = []
    for result in pipeline(text, voice=reference_voice, speed=float(prod["baseSpeed"])):
        audio = result[2] if isinstance(result, tuple) else getattr(result, "audio", None)
        if audio is not None:
            kokoro_parts.append(np.asarray(audio, dtype=np.float32).reshape(-1))
    if not kokoro_parts:
        raise RuntimeError("Kokoro returned no usable speech")
    kokoro = np.concatenate(kokoro_parts)
    duration = save_audio(OUT / "01-kokoro-michael.wav", kokoro, 24000)
    report["samples"]["kokoro"] = {
        "filename": "01-kokoro-michael.wav", "voice": reference_voice,
        "nativeSpeed": prod["baseSpeed"], "sampleSeconds": round(duration, 2),
        "totalSeconds": round(time.perf_counter() - t0, 2),
        "wpm": round(len(text.split()) * 60 / max(0.1, duration), 1),
    }
    # Chatterbox requires >=5 seconds; using 11s of clean, owner-generated
    # Kokoro baseline holds the timbre reasonably consistent across models.
    reference = normalize_audio(kokoro)
    reference_secs = min(11.0, len(reference) / 24000)
    sf.write(str(OUT / "reference-kokoro-michael.wav"), reference[:int(reference_secs*24000)],
             24000, subtype="PCM_16")
    report["referenceSeconds"] = round(reference_secs, 2)
    write_report(report)
    del pipeline, kokoro, kokoro_parts
    gc.collect()

    from chatterbox.tts_turbo import ChatterboxTurboTTS

    for name, nano, filename in [
        ("nano", True, "02-chatterbox-nano.wav"),
        ("turbo", False, "03-chatterbox-turbo.wav"),
    ]:
        print(f"Starting {name} on CPU", flush=True)
        t0 = time.perf_counter()
        model = None
        try:
            model = ChatterboxTurboTTS.from_pretrained(device="cpu", nano=nano)
            model_load = time.perf_counter() - t0
            t1 = time.perf_counter()
            with torch.inference_mode():
                waveform = model.generate(
                    text, audio_prompt_path=str(OUT / "reference-kokoro-michael.wav"),
                    temperature=0.75, repetition_penalty=1.22,
                )
            generation_seconds = time.perf_counter() - t1
            seconds = save_audio(OUT / filename, waveform, model.sr)
            report["samples"][name] = {
                "filename": filename, "modelLabel": model.model_label,
                "modelLoadAndDownloadSeconds": round(model_load, 2),
                "inferenceSeconds": round(generation_seconds, 2),
                "sampleSeconds": round(seconds, 2),
                "realtimeFactor": round(generation_seconds / max(0.1, seconds), 2),
                "wpm": round(len(text.split()) * 60 / max(0.1, seconds), 1),
            }
            print(f"{name}: {seconds:.1f}s speech in {generation_seconds:.1f}s inference", flush=True)
        except Exception as exc:
            report["samples"][name] = {"error": str(exc), "traceback": traceback.format_exc()[-3000:]}
            print(f"FAILED {name}: {exc}", flush=True)
        finally:
            write_report(report)
            if model is not None:
                del model
            gc.collect()
    missing = [x for x in ("kokoro", "nano", "turbo") if "filename" not in report["samples"].get(x, {})]
    if missing:
        raise SystemExit(f"Voice comparison incomplete; missing {', '.join(missing)}. See report.")


if __name__ == "__main__":
    main()
