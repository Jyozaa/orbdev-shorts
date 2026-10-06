#!/usr/bin/env python3
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import capture_sources
import prepare_render_props as render
import check_visual_quality as quality

def beat(text,role="fact"):
    return {"text":text,"editorialRole":role,"visual":{"type":"kinetic","text":"TEMP"},"start":0.0,"end":1.2}

def main():
    # GitHub repository pages hide useful README attachments from the normal HTML
    # image scraper. Ensure the raw README path exposes demos without an API key.
    sample=b"""
## Dot computers
https://github.com/user-attachments/assets/11111111-1111-1111-1111-111111111111
_Computer activity, browser and saved files appear inline._
## Calls
![call demo](https://example.com/call-demo.png)
![badge](https://img.shields.io/badge/test-blue.svg)
"""
    saved=capture_sources.fetch
    try:
        capture_sources.fetch=lambda *args,**kwargs:(sample,"text/plain")
        found=capture_sources.github_readme_candidates("https://github.com/CopilotKit/OpenDots")
    finally:
        capture_sources.fetch=saved
    urls=[x["url"] for x in found]
    assert any("user-attachments/assets" in x for x in urls),urls
    assert "https://example.com/call-demo.png" in urls
    assert not any("shields.io" in x for x in urls)
    assert any("Dot computers" in str(x.get("text")) for x in found)

    beats=[
        beat("The interface shows live computer activity"),
        beat("A saved file stays in the workspace"),
        beat("The agent can continue through calls"),
        beat("Slack messages reach the specialist"),
        beat("A router moves work between tools","explanation"),
        beat("Performance improves with caching","explanation"),
        beat("This is a caveat","caveat"),
        beat("Final result","reaction"),
    ]
    source_assets={"0":{"assets":[
        {"src":"computer.jpg","text":"Dot computers live computer activity browser workspace","baseScore":88,"width":1200,"height":700,"visualHash":"0000000000000000"},
        {"src":"files.jpg","text":"workspace saved files persist stop start","baseScore":88,"width":1200,"height":700,"visualHash":"ffffffffffffffff"},
        {"src":"calls.jpg","text":"text calls realtime speech conversation","baseScore":88,"width":1200,"height":700,"visualHash":"aaaaaaaaaaaaaaaa"},
        {"src":"slack.jpg","text":"Slack specialist messages channels integration","baseScore":88,"width":1200,"height":700,"visualHash":"5555555555555555"},
    ]}}
    story={"editorial":{"sources":[{"publisher":"GITHUB"}]}}
    used=set();hashes=[]
    enriched=render.apply_source_enrichment(beats,source_assets,story,used,hashes)
    assert enriched>=3,enriched
    assert len({b["visual"].get("src") for b in beats if b["visual"].get("type")=="source"})==enriched
    assert len(used)==enriched

    # When a technical story has plenty of verified media, a 100%-diagram edit
    # should fail rather than ignoring all of that source material.
    props={
        "sourceCandidateCount":6,
        "beats":[beat("Explain routing","explanation"),beat("Explain tools","explanation")],
        "visualBeats":[
            {"visual":{"type":"drawn-diagram","kind":"branch"}},
            {"visual":{"type":"drawn-diagram","kind":"orbit","continuityKey":"x","transition":"morph"}},
            {"visual":{"type":"drawn-diagram","kind":"flow"}},
            {"visual":{"type":"drawn-diagram","kind":"stack"}},
            {"visual":{"type":"drawn-diagram","kind":"mesh"}},
            {"visual":{"type":"drawn-diagram","kind":"growth"}},
            {"visual":{"type":"metric","value":"2x"}},
            {"visual":{"type":"drawn-diagram","kind":"timeline"}},
        ],
    }
    result=quality.audit(props)
    assert not result["passed"] and any("Rich verified media" in x for x in result["issues"]),result
    print("source-media enrichment regression checks passed")

if __name__=="__main__":main()
