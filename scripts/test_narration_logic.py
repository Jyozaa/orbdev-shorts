from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import generate_narration as g

def main():
    profile={
        "chunkTargetWords":11,"chunkMaxWords":16,"chunkMinWords":5,
        "targetWpm":188,"postTempoMin":0.985,"postTempoMax":1.025,
        "nativeRetargetToleranceWpm":6,"nativeRetargetMinMultiplier":0.94,"nativeRetargetMaxMultiplier":1.07,
    }
    story={"narration":"Sony made the old console smarter. The new network is smaller, but there is one problem: it is still not the Pro.",
      "beats":[
        {"text":"Sony made","editorialRole":"setup"},
        {"text":"the old console smarter.","editorialRole":"fact"},
        {"text":"The new network is smaller,","editorialRole":"explanation"},
        {"text":"but there is one problem:","editorialRole":"reaction"},
        {"text":"it is still not the Pro.","editorialRole":"punchline"},
      ]}
    chunks=g.plan_speech_chunks(story,profile)
    assert len(chunks)>=3,chunks
    assert any(c["role"]=="reaction" for c in chunks),chunks
    assert any(c["role"]=="punchline" for c in chunks),chunks
    assert all(c["wordCount"]<=16 for c in chunks),chunks
    assert abs(g.choose_post_tempo(188,profile)-1.0)<0.001
    assert g.choose_post_tempo(160,profile)<=1.025
    assert g.choose_post_tempo(210,profile)>=0.985
    adjusted=g.native_retarget_speed(1.18,165,profile)
    assert adjusted>1.18
    print("Narration logic regression checks passed")

if __name__=="__main__":
    main()
