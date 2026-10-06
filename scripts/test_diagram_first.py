#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import prepare_render_props as render
import check_visual_quality as quality

def beat(text,role,visual):
    return {"text":text,"editorialRole":role,"visual":visual,"start":0.0,"end":1.5}

def main():
    items=[
        beat("A sandbox blocks unwanted access","explanation",{"type":"kinetic","text":"SANDBOX ACCESS"}),
        beat("A router sends tokens through specialist experts","explanation",{"type":"text","text":"TOKEN ROUTER"}),
        beat("Speech becomes an audio signal before decoding","explanation",{"type":"symbol","symbol":"AUDIO"}),
        beat("Naturally this went perfectly","joke",{"type":"kinetic","text":"SURE IT DID"}),
        beat("Wait, what?","reaction",{"type":"kinetic","text":"WAIT WHAT"}),
    ]
    assert render.apply_diagram_first(items)==4
    assert items[0]["visual"]["kind"]=="shield"
    assert items[1]["visual"]["kind"]=="branch"
    assert items[2]["visual"]["kind"]=="wave"
    assert items[3]["visual"]["type"]=="drawn-diagram"
    assert items[4]["visual"]["type"]=="kinetic"
    for item in items[:4]:
        assert item["visual"]["type"]=="drawn-diagram"
        assert all(len(x.split())<=2 and len(x)<=22 for x in item["visual"].get("labels",[]))

    rejected=beat("Requests flow through a model and return results","explanation",
                  {"type":"source","sourceIndex":0,"query":"missing"})
    render.apply_diagram_first([rejected])
    assert rejected["visual"]["type"]=="drawn-diagram"

    bad={"beats":[beat("A model routes tokens","explanation",{"type":"kinetic","text":"MODEL ROUTES"})]*4,
         "visualBeats":[
            {"visual":{"type":"kinetic","text":"LOTS OF WORDS HERE"}},
            {"visual":{"type":"kinetic","text":"MORE LARGE WORDS HERE"}},
            {"visual":{"type":"source","src":"a.jpg","visualHash":"1111111111111111"}},
            {"visual":{"type":"metric","value":"2x"}},
            {"visual":{"type":"source","src":"b.jpg","visualHash":"2222222222222222"}},
            {"visual":{"type":"kinetic","text":"STILL TOO MUCH TEXT"}},
            {"visual":{"type":"metric","value":"3x"}},
            {"visual":{"type":"source","src":"c.jpg","visualHash":"3333333333333333"}},
         ]}
    assert not quality.audit(bad)["passed"]

    good={"beats":[
            beat("A router splits tokens","explanation",{"type":"drawn-diagram","kind":"branch"}),
            beat("Tools connect around it","explanation",{"type":"drawn-diagram","kind":"orbit"}),
            beat("The result flows out","transition",{"type":"drawn-diagram","kind":"flow"}),
          ],
          "visualBeats":[
            {"visual":{"type":"source","src":"a.jpg","visualHash":"1111111111111111"}},
            {"visual":{"type":"drawn-diagram","kind":"branch","continuityKey":"x","transition":"morph"}},
            {"visual":{"type":"drawn-diagram","kind":"orbit","continuityKey":"x","transition":"morph"}},
            {"visual":{"type":"source","src":"b.jpg","visualHash":"2222222222222222"}},
            {"visual":{"type":"drawn-diagram","kind":"flow"}},
            {"visual":{"type":"metric","value":"2x"}},
            {"visual":{"type":"source","src":"c.jpg","visualHash":"3333333333333333"}},
            {"visual":{"type":"drawn-diagram","kind":"growth"}},
          ]}
    result=quality.audit(good)
    assert result["passed"],result
    assert result["diagramFraction"]>=0.5
    print("diagram-first production regression checks passed")

if __name__=="__main__":main()
