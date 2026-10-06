#!/usr/bin/env python3
"""Small offline image-selection, identity and quality-gate regression tests."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import prepare_render_props as render
import check_visual_quality as quality
from story_identity import duplicate

def run():
    assets={"assets":[
        {"src":"a.jpg","text":"AI example release","url":"https://example.com/ai/release","baseScore":99,"visualHash":"5555555555555555"},
        {"src":"same.jpg","text":"AI example release","url":"https://example.com/ai/release","baseScore":90,"visualHash":"5555555555555555"},
        {"src":"different.jpg","text":"AI example release","url":"https://example.com/ai/release","baseScore":80,"visualHash":"aaaaaaaaaaaaaaaa"}]}
    selected=set();hashes=[]
    first,_=render.choose_source(assets,"AI example release",[],selected,True,hashes)
    assert first["src"]=="a.jpg"
    selected.add(first["src"]);hashes.append(first["visualHash"])
    second,_=render.choose_source(assets,"AI example release",[],selected,True,hashes)
    assert second["src"]=="different.jpg"
    selected.add(second["src"]);hashes.append(second["visualHash"])
    assert render.choose_source(assets,"AI example release",[],selected,True,hashes)[0] is None
    assert render.kinetic_from_beat({"text":"The model processes images","editorialRole":"fact"})["type"]=="fact"
    x={"title":"AMD World Labs acquisition","slug":"amd-world-labs",
       "editorial":{"sources":[{"url":"https://example.com/world-labs/?ref=foo","primary":True}]}}
    y={"headline":"AMD buys World Labs","sourceUrls":["https://example.com/world-labs"]}
    assert duplicate(x,y)
    assert not duplicate(x,{"title":"A compiler rewrite","sourceUrls":["https://another.com/compiler"]})
    props={"visualBeats":[{"visual":{"type":"source","src":"a.jpg","visualHash":"5555555555555555"}},
                          {"visual":{"type":"source","src":"a.jpg","visualHash":"5555555555555555"}}]}
    assert not quality.audit(props)["passed"]
    props["visualBeats"][1]["visual"]={"type":"fact","headline":"New scene"}
    assert quality.audit(props)["passed"]
    print("visual/identity tests: PASS")

if __name__=="__main__":run()
