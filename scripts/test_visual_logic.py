#!/usr/bin/env python3
"""Small offline image-selection, identity and quality-gate regression tests."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import prepare_render_props as render
import check_visual_quality as quality
from story_identity import duplicate, file_sha256, story_plan_sha256
from filter_queue import filter_paths
from mark_covered import merge_receipts
import tempfile

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
    fallback=render.kinetic_from_beat({"text":"The model processes images very differently","editorialRole":"fact"})
    assert fallback["type"]=="kinetic" and len(fallback["text"].split())<=4
    original={"title":"AMD World Labs acquisition","slug":"amd-world-labs",
              "narration":"AMD is buying World Labs.",
              "beats":[{"text":"AMD is buying World Labs.","visual":{"type":"metric","value":"$8B"}}],
              "editorial":{"storyKey":"amd-world-labs",
                           "sources":[{"url":"https://example.com/world-labs","primary":True}]}}
    same_topic_new_video={"title":"AMD buys World Labs","slug":"another-amd-angle",
              "narration":"AMD now owns a spatial intelligence company.",
              "beats":[{"text":"AMD now owns a spatial intelligence company.",
                        "visual":{"type":"explain","mode":"pipeline","stages":["AMD","World Labs"]}}],
              "editorial":{"storyKey":"amd-world-labs",
                           "sources":[{"url":"https://example.com/world-labs","primary":True}]}}
    identical_video_different_title={**original,"slug":"renamed","title":"Breaking: AMD World Labs",
                                     "publish":{"youtubeTitle":"Different metadata"}}
    assert not duplicate(original,same_topic_new_video), "New creative angle on same news must be allowed"
    assert duplicate(original,identical_video_different_title), "Renaming the same storyboard is not a new video"
    assert story_plan_sha256(original) == story_plan_sha256(identical_video_different_title)
    assert not duplicate(original,{"headline":"AMD buys World Labs","sourceUrls":["https://example.com/world-labs"]})
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"clip.mp4"
        path.write_bytes(b"real render bytes")
        h=file_sha256(path)
        previous=[{"storyKey":"same","youtubeVideoId":"abc","videoSha256":h}]
        assert len(h)==64 and h==file_sha256(path)
        updated=merge_receipts(previous,[{"storyKey":"same","youtubeVideoId":"def","videoSha256":"b"*64}])
        assert len(updated)==2, "A second Short on the same topic must not overwrite its predecessor"
        file_a=Path(temp)/"a.json";file_b=Path(temp)/"b.json";file_c=Path(temp)/"c.json"
        file_a.write_text(__import__("json").dumps(original))
        file_b.write_text(__import__("json").dumps(same_topic_new_video))
        file_c.write_text(__import__("json").dumps(identical_video_different_title))
        chosen=filter_paths([str(file_a),str(file_b),str(file_c)],
                            [str(file_a),str(file_b),str(file_c)],[])
        assert len(chosen)==2, f"One exact storyboard duplicate should be suppressed: {chosen}"
        chosen=filter_paths([str(file_b)],[str(file_a),str(file_b)],
                            [{"storyPlanSha256":story_plan_sha256(original),"youtubeVideoId":"previous"}])
        assert chosen==[str(file_b)], "An old topic must not block a new take"
    props={"visualBeats":[{"visual":{"type":"source","src":"a.jpg","visualHash":"5555555555555555"}},
                          {"visual":{"type":"source","src":"a.jpg","visualHash":"5555555555555555"}}]}
    assert not quality.audit(props)["passed"]
    props["visualBeats"][1]["visual"]={"type":"fact","headline":"New scene"}
    assert quality.audit(props)["passed"]
    print("visual/identity tests: PASS")

if __name__=="__main__":run()
