#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import prepare_render_props as render

def d(kind):
    return {"text":kind,"start":0.0,"end":1.4,
            "visual":{"type":"drawn-diagram","kind":kind,"labels":["A","B"]}}

def main():
    candidate=d("orbit")
    chosen,forced=render.choose_window_candidate(
        [candidate],[0],"abstract-tech","drawn-diagram","branch",None,
        0,3,1,4,set(),0,2)
    assert chosen==0 and forced is False, "different drawn families should continue"
    same=d("branch")
    _,forced_same=render.choose_window_candidate(
        [same],[0],"abstract-tech","drawn-diagram","branch",None,
        0,3,1,4,set(),0,2)
    assert forced_same is True, "same-family abstract repetition should reset"

    windows=[d("branch"),d("orbit"),d("flow")]
    for i,w in enumerate(windows):
        w["start"]=i*1.4;w["end"]=(i+1)*1.4
    render.apply_diagram_continuity(windows)
    keys=[w["visual"].get("continuityKey") for w in windows]
    assert keys[0] and len(set(keys))==1
    assert all(w["visual"].get("transition")=="morph" for w in windows)
    assert windows[0]["visual"].get("continuityOut") is True
    assert windows[1]["visual"].get("continuityIn") is True
    assert windows[1]["visual"].get("continuityOut") is True
    assert windows[2]["visual"].get("continuityIn") is True
    render.assert_visual_window_diversity(windows,3,4,2)

    broken=[d("branch"),d("branch")]
    for i,w in enumerate(broken):
        w["start"]=i;w["end"]=i+1
    render.apply_diagram_continuity(broken)
    try:
        render.assert_visual_window_diversity(broken,3,4,2)
    except RuntimeError:
        pass
    else:
        raise AssertionError("same-family back-to-back diagrams should not pass")
    print("diagram continuity regression checks passed")

if __name__=="__main__":main()
