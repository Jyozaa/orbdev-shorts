from __future__ import annotations
import copy,json,math,re,sys
from pathlib import Path

BUILD_DIR=Path("build"); CAPTIONS_PATH=Path("public/captions.json"); MEME_SELECTION_PATH=BUILD_DIR/"meme-selection.json"
SOURCE_ASSETS_PATH=BUILD_DIR/"source-assets.json"; LOGO_ASSETS_PATH=BUILD_DIR/"logo-assets.json"; CUTAWAYS_PATH=BUILD_DIR/"cutaways.json"
MIN_VISUAL_SECONDS=1.8; TARGET_VISUAL_SECONDS=2.35; MAX_VISUAL_SECONDS=3.35
SOURCE_MIN_MATCH=0.34
SFX_DURATIONS={"whoosh":.34,"impact":.42,"scratch":.48,"tick":.10}
STOP={"the","a","an","and","or","to","for","of","in","on","with","is","are","was","were","it","this","that","from","your","our","their","just","new"}

def norm(t:str)->str:return re.sub(r"[^a-z0-9]+","",t.lower())
def tokens(t:str)->set[str]:
    return {x for x in re.sub(r"[^a-z0-9]+"," ",t.lower()).split() if len(x)>1 and x not in STOP}
def beat_tokens(t:str)->list[str]:return [x for x in (norm(v) for v in re.findall(r"\S+",t)) if x]

def find_sequence(words,expected,cursor):
    normalized=[norm(str(w["text"])) for w in words]
    for start in range(cursor,min(len(words),cursor+10)):
        end=start+len(expected)
        if normalized[start:end]==expected:return start,end-1
    return cursor,min(len(words)-1,cursor+max(1,len(expected))-1)

def attach_logos(v,logos):
    if v.get("type")=="logo":
        slug=str(v.get("slug","")).lower()
        if slug in logos:v["src"]=logos[slug]
    elif v.get("type")=="flow":
        for n in v.get("nodes",[]):
            if isinstance(n,dict) and n.get("kind")=="logo":
                slug=str(n.get("slug","")).lower()
                if slug in logos:n["src"]=logos[slug]

def source_match(asset:dict,query:str)->float:
    q=tokens(query); a=tokens(f'{asset.get("text","")} {asset.get("url","")}')
    if not q or not a:return 0.0
    overlap=len(q&a)
    if overlap==0:return 0.0
    coverage=overlap/max(1,len(q))
    precision=overlap/max(1,min(len(a),8))
    return round(min(1.0,.82*coverage+.18*precision),3)

def choose_source(entry:object,query:str):
    if isinstance(entry,str):return entry,0.35
    if not isinstance(entry,dict):return None,0.0
    assets=entry.get("assets",[])
    if not isinstance(assets,list):return None,0.0
    scored=[(source_match(a,query),int(a.get("baseScore",0)),a) for a in assets if isinstance(a,dict)]
    scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
    if not scored or scored[0][0]<SOURCE_MIN_MATCH:return None,(scored[0][0] if scored else 0.0)
    return scored[0][2].get("src"),scored[0][0]

def family(kind:str)->str:
    if kind=="explain":return "explain"
    if kind=="source":return "source"
    if kind in {"chart","metric"}:return "data"
    if kind in {"timeline"}:return "timeline"
    if kind in {"logo"}:return "brand"
    if kind in {"comparison"}:return "comparison"
    if kind in {"flow","diagram","network"}:return "generic-diagram"
    return "minimal"

def visual_weight(beat,prev_family=None)->float:
    v=beat.get("visual",{}); kind=str(v.get("type","text"))
    base={"explain":12,"chart":8.5,"comparison":8.2,"timeline":8,"source":7.5,"logo":7.2,"network":6,"flow":5.5,"diagram":5.2,"metric":5,"symbol":4,"text":2}.get(kind,1)
    if kind=="source":
        match=float(v.get("matchScore",0))
        if not v.get("src") or match<SOURCE_MIN_MATCH:return -10
        base+=match*2
    fam=family(kind)
    if prev_family:
        base+=1.6 if fam!=prev_family else -2.4
    return base

def build_visual_windows(beats,cutaway_by_beat,final_duration):
    windows=[]; index=0; prev_family=None
    while index<len(beats):
        start_index=index; end_index=index; start=float(beats[index]["start"]); end=float(beats[index]["end"])
        while end_index+1<len(beats):
            if end_index in cutaway_by_beat:break
            current=end-start
            if current>=TARGET_VISUAL_SECONDS:break
            next_end=float(beats[end_index+1]["end"]); proposed=next_end-start
            if proposed>MAX_VISUAL_SECONDS and current>=MIN_VISUAL_SECONDS:break
            end_index+=1; end=next_end
            if end_index in cutaway_by_beat or end-start>=TARGET_VISUAL_SECONDS:break
        candidates=list(range(start_index,end_index+1))
        chosen=max(candidates,key=lambda i:(visual_weight(beats[i],prev_family),float(beats[i]["end"])-float(beats[i]["start"]),-i))
        vb=copy.deepcopy(beats[chosen]); vb["start"]=round(start,4); vb["end"]=round(end,4)
        vb.pop("meme",None);vb.pop("memeIntent",None);vb.pop("sfx",None)
        if visual_weight(vb,prev_family)<0:
            fallback=max(candidates,key=lambda i:visual_weight(beats[i],prev_family))
            vb=copy.deepcopy(beats[fallback]);vb["start"]=round(start,4);vb["end"]=round(end,4)
            vb.pop("meme",None);vb.pop("memeIntent",None);vb.pop("sfx",None)
        windows.append(vb);prev_family=family(str(vb.get("visual",{}).get("type","text")));index=end_index+1
    if windows and float(windows[-1]["end"])<final_duration:windows[-1]["end"]=round(final_duration,4)
    return windows

def main():
    if len(sys.argv)!=2:raise SystemExit("usage: prepare_render_props.py <story.json>")
    story=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"));timing=json.loads(CAPTIONS_PATH.read_text(encoding="utf-8"))
    words=timing["words"];final_duration=max(1.0,float(timing["durationSeconds"])+.10)
    selections=json.loads(MEME_SELECTION_PATH.read_text(encoding="utf-8")) if MEME_SELECTION_PATH.exists() else {}
    source_assets=json.loads(SOURCE_ASSETS_PATH.read_text(encoding="utf-8")) if SOURCE_ASSETS_PATH.exists() else {}
    logos=json.loads(LOGO_ASSETS_PATH.read_text(encoding="utf-8")) if LOGO_ASSETS_PATH.exists() else {}
    cutaways=json.loads(CUTAWAYS_PATH.read_text(encoding="utf-8")) if CUTAWAYS_PATH.exists() else []
    cutaway_by_beat={int(x["beatIndex"]):x for x in cutaways}
    prepared=[];cursor=0
    for index,beat in enumerate(story["beats"]):
        expected=beat_tokens(beat["text"]);si,ei=find_sequence(words,expected,cursor);cursor=ei+1
        adjusted=dict(beat);adjusted["visual"]=json.loads(json.dumps(beat["visual"]))
        adjusted["start"]=round(float(words[si]["startMs"])/1000,4);adjusted["end"]=round(float(words[ei]["endMs"])/1000,4)
        v=adjusted["visual"]
        if v.get("type")=="source":
            source_index=int(v.get("sourceIndex",0));key=str(source_index);sources=story.get("editorial",{}).get("sources",[])
            if 0<=source_index<len(sources):v["publisher"]=sources[source_index].get("publisher","SOURCE")
            query=str(v.get("query") or beat["text"]);src,score=choose_source(source_assets.get(key),query)
            v["matchScore"]=score
            if src:v["src"]=src
            print(f'Source beat {index}: query="{query}" match={score:.3f} src={src or "REJECTED"}')
        attach_logos(v,logos)
        selected=selections.get(str(index))
        if selected and selected.get("presentation")!="cutaway":adjusted["meme"]=dict(selected)
        prepared.append(adjusted)

    if prepared:
        prepared[0]["start"]=0.0
        for i in range(len(prepared)-1):
            prepared[i]["end"]=float(cutaway_by_beat[i]["start"]) if i in cutaway_by_beat else prepared[i+1]["start"]
        last=len(prepared)-1;prepared[last]["end"]=float(cutaway_by_beat[last]["start"]) if last in cutaway_by_beat else final_duration
        for beat in prepared:
            start=float(beat["start"]);end=float(beat["end"]);dur=max(.01,end-start)
            sfx=beat.get("sfx")
            if isinstance(sfx,str) and sfx in SFX_DURATIONS:final_duration=max(final_duration,start+SFX_DURATIONS[sfx]+.08)
            if "meme" not in beat:continue
            meme=beat["meme"];md=float(meme["durationSeconds"]);media=str(meme.get("mediaType",""))
            if media=="audio":
                meme["durationSeconds"]=round(md,3);meme["offsetSeconds"]=round(max(.02,dur-.16),3)
                final_duration=max(final_duration,start+float(meme["offsetSeconds"])+md+.08)
            else:
                use=min(md,max(.35,dur-.05));meme["durationSeconds"]=round(use,3);meme["offsetSeconds"]=round(max(.02,dur-use-.03),3)
        if last not in cutaway_by_beat:prepared[last]["end"]=round(final_duration,4)

    visual_beats=build_visual_windows(prepared,cutaway_by_beat,final_duration)
    props=dict(story);props["durationSeconds"]=round(final_duration,4);props["beats"]=prepared;props["visualBeats"]=visual_beats;props["captions"]=words;props["cutaways"]=cutaways
    BUILD_DIR.mkdir(parents=True,exist_ok=True);(BUILD_DIR/"render-props.json").write_text(json.dumps(props,indent=2),encoding="utf-8")
    print(f"Render props ready: {len(prepared)} semantic beats -> {len(visual_beats)} visual windows, {final_duration:.2f}s")
    print("Visual treatments:",[b["visual"]["type"] for b in visual_beats])
    print("Visual holds:",[round(float(b["end"])-float(b["start"]),2) for b in visual_beats])

if __name__=="__main__":main()
