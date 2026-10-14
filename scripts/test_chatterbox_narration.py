"""Lightweight contract tests for the Turbo -> Nano chain (no model download)."""
from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

import chatterbox_narration as c
import generate_narration as g


class FakeVoice:
    def __init__(self, should_fail: bool = False):
        self.sr = 24000
        self.should_fail = should_fail
        self.reference_used = False

    def prepare_conditionals(self, path: str):
        assert path
        self.reference_used = True

    def generate(self, text: str, **kwargs):
        assert self.reference_used
        assert kwargs["temperature"] == 0.75
        if self.should_fail:
            raise RuntimeError("Synthetic inference failure")
        duration = max(1.4, len(text.split()) / 3.0)
        t = np.arange(round(self.sr * duration)) / self.sr
        return 0.06 * np.sin(2 * math.pi * 170 * t).astype("float32")


def main():
    story={"narration":"The model routes requests. Then specialist tools return results."}
    chunks=c.plan_chatterbox_chunks(story["narration"],target=4,maximum=7)
    assert " ".join(chunks)==story["narration"],chunks
    assert len(chunks)==2,chunks
    assert c.sentence_units("The result is 3.46 billion. That's it.")==[
        "The result is 3.46 billion.","That's it."
    ]
    assert c.plan_chatterbox_chunks("")==[]

    profile={"engine":"chatterbox","voice":"am_michael","targetWpm":176,
             "temperature":0.75,"repetitionPenalty":1.22,
             "chunkTargetWords":4,"chunkMaxWords":7,"chunkPauseMs":60}
    with tempfile.TemporaryDirectory() as td:
        audio=Path(td)/"voice.wav"
        reference=Path(td)/"reference.wav"
        calls=[]
        def loader(*,device,nano):
            calls.append(nano)
            return FakeVoice() if nano else FakeVoice(should_fail=True)
        captions,report,metadata=c.render_chatterbox_with_fallback(
            story,profile,output=audio,reference=reference,
            loader=loader,reference_factory=lambda path,voice:path
        )
        assert calls==[False,True],calls
        assert audio.is_file()
        assert metadata["engine"]=="chatterbox-nano"
        assert metadata["usedFallback"] is True
        assert metadata["fallbackFailures"][0]["engine"]=="chatterbox-turbo"
        assert len(report)==2
        assert len(captions)==len(story["narration"].split())
        assert all(a["endMs"]>a["startMs"] for a in captions)
        assert sf.info(audio).duration>2.5

        calls.clear()
        captions,report,metadata=c.render_chatterbox_with_fallback(
            story,profile,output=audio,reference=reference,
            loader=lambda *,device,nano:(calls.append(nano) or FakeVoice()),
            reference_factory=lambda path,voice:path
        )
        assert calls==[False] and metadata["engine"]=="chatterbox-turbo"
        assert not metadata["usedFallback"]

        def broken(*,device,nano):
            raise RuntimeError("Neither engine is available")
        try:
            c.render_chatterbox_with_fallback(
                story,profile,output=audio,reference=reference,
                loader=broken,reference_factory=lambda path,voice:path
            )
            raise AssertionError("Both failing should stop publishing")
        except RuntimeError as exc:
            assert "Both Chatterbox Turbo and Nano failed" in str(exc)
        assert not audio.exists(),"Stale audio must not survive total TTS failure"

    p=json.loads(Path("editorial/narration-profiles.json").read_text())
    assert p["defaultProfile"]=="orbdev-chatterbox"
    new=p["profiles"]["orbdev-chatterbox"]
    assert new["primaryModel"]=="chatterbox-turbo"
    assert new["fallbackModel"]=="chatterbox-nano"
    assert 1.0 <= g.choose_post_tempo(152,new) <= 1.17
    assert g.choose_post_tempo(200,new)==1.0,"Do not speed up already-fast narration"
    print("Turbo/Nano voice selection and fail-closed regression checks passed")


if __name__=="__main__":
    main()
