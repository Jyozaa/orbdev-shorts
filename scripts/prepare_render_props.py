from __future__ import annotations
import copy,json,math,re,sys
from pathlib import Path

BUILD_DIR=Path("build"); CAPTIONS_PATH=Path("public/captions.json"); MEME_SELECTION_PATH=BUILD_DIR/"meme-selection.json"
SOURCE_ASSETS_PATH=BUILD_DIR/"source-assets.json"; LOGO_ASSETS_PATH=BUILD_DIR/"logo-assets.json"; CUTAWAYS_PATH=BUILD_DIR/"cutaways.json"
MIN_VISUAL_SECONDS=1.8; TARGET_VISUAL_SECONDS=2.35; MAX_VISUAL_SECONDS=3.35
SOURCE_MIN_MATCH=0.34
SFX_DURATIONS={"whoosh":.34,"impact":.42,"scratch":.48,"tick":.10}
STOP={"the","a","an","and","or","to","for","of","in","on","with","is","are","was","were","it","this","that","from","your","our","their","just","new","image","images","game","gameplay","hardware","console","quality","comparison","detail","official","article"}

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

def choose_source(entry:object,query:str,must_match:list[str],used:set[str],allow_reuse:bool):
    if isinstance(entry,str):
        if used and not allow_reuse and entry in used:return None,0.0
        return entry,0.35
    if not isinstance(entry,dict):return None,0.0
    assets=entry.get("assets",[])
    if not isinstance(assets,list):return None,0.0
    required=[norm(v) for v in must_match if isinstance(v,str) and norm(v)]
    scored=[]
    for asset in assets:
        if not isinstance(asset,dict):continue
        src=str(asset.get("src",""))
        if not src:continue
        if src in used and not allow_reuse:continue
        searchable=norm(f'{asset.get("text","")} {asset.get("url","")}')
        if required and not all(term in searchable for term in required):
            continue
        scored.append((source_match(asset,query),int(asset.get("baseScore",0)),asset))
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

def base_visual_weight(beat)->float:
    v=beat.get("visual",{}); kind=str(v.get("type","text"))
    base={
        "explain":9.2,
        "source":9.0,
        "comparison":8.8,
        "chart":8.6,
        "timeline":8.5,
        "logo":8.3,
        "metric":6.8,
        "network":6.0,
        "flow":5.6,
        "diagram":5.4,
        "symbol":4.8,
        "text":3.2,
    }.get(kind,1.0)
    if kind=="source":
        match=float(v.get("matchScore",0))
        if not v.get("src") or match<SOURCE_MIN_MATCH:return -10
        base+=match*2.2
    return base

def candidate_score(beat,prev_family=None,prev_explain_mode=None)->float:
    v=beat.get("visual",{});kind=str(v.get("type","text"));fam=family(kind)
    score=base_visual_weight(beat)
    if prev_family:
        score += 1.4 if fam!=prev_family else -3.0
    if kind=="explain":
        mode=str(v.get("mode",""))
        if prev_explain_mode and mode==prev_explain_mode:
            score-=3.0
    return score

def choose_window_candidate(beats,candidates,prev_family,prev_explain_mode,explain_count,max_explain):
    viable=[i for i in candidates if base_visual_weight(beats[i])>=0]
    if not viable: viable=list(candidates)

    non_explain=[i for i in viable if str(beats[i].get("visual",{}).get("type",""))!="explain"]

    # Explanations are high-value, but they should not become the entire edit.
    # If the previous window was already an explanation, use a valid alternative.
    if prev_family=="explain" and non_explain:
        viable=non_explain
    elif explain_count>=max_explain and non_explain:
        viable=non_explain

    # Avoid repeating the exact same explanation grammar when alternatives exist.
    if prev_explain_mode:
        different=[
            i for i in viable
            if not (
                str(beats[i].get("visual",{}).get("type",""))=="explain"
                and str(beats[i].get("visual",{}).get("mode",""))==prev_explain_mode
            )
        ]
        if different:
            viable=different

    return max(
        viable,
        key=lambda i:(
            candidate_score(beats[i],prev_family,prev_explain_mode),
            float(beats[i]["end"])-float(beats[i]["start"]),
            -i,
        ),
    )

def build_visual_windows(beats,cutaway_by_beat,final_duration):
    windows=[];index=0;prev_family=None;prev_explain_mode=None;explain_count=0
    # Roughly 25-35% of final windows may be explanatory animations.
    max_explain=max(2,min(4,math.floor(final_duration/9.5)))

    while index<len(beats):
        start_index=index;end_index=index;start=float(beats[index]["start"]);end=float(beats[index]["end"])

        while end_index+1<len(beats):
            if end_index in cutaway_by_beat:break
            current=end-start
            if current>=TARGET_VISUAL_SECONDS:break
            next_end=float(beats[end_index+1]["end"]);proposed=next_end-start
            if proposed>MAX_VISUAL_SECONDS and current>=MIN_VISUAL_SECONDS:break
            end_index+=1;end=next_end
            if end_index in cutaway_by_beat or end-start>=TARGET_VISUAL_SECONDS:break

        candidates=list(range(start_index,end_index+1))
        chosen=choose_window_candidate(
            beats,candidates,prev_family,prev_explain_mode,explain_count,max_explain
        )

        vb=copy.deepcopy(beats[chosen]);vb["start"]=round(start,4);vb["end"]=round(end,4)
        vb.pop("meme",None);vb.pop("memeIntent",None);vb.pop("sfx",None)
        windows.append(vb)

        kind=str(vb.get("visual",{}).get("type","text"))
        prev_family=family(kind)
        if kind=="explain":
            explain_count+=1
            prev_explain_mode=str(vb.get("visual",{}).get("mode",""))
        else:
            prev_explain_mode=None

        index=end_index+1

    if windows and float(windows[-1]["end"])<final_duration:
        windows[-1]["end"]=round(final_duration,4)

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
    prepared=[];cursor=0;used_source_assets:set[str]=set()
    for index,beat in enumerate(story["beats"]):
        expected=beat_tokens(beat["text"]);si,ei=find_sequence(words,expected,cursor);cursor=ei+1
        adjusted=dict(beat);adjusted["visual"]=json.loads(json.dumps(beat["visual"]))
        adjusted["start"]=round(float(words[si]["startMs"])/1000,4);adjusted["end"]=round(float(words[ei]["endMs"])/1000,4)
        v=adjusted["visual"]
        if v.get("type")=="source":
            source_index=int(v.get("sourceIndex",0));key=str(source_index);sources=story.get("editorial",{}).get("sources",[])
            if 0<=source_index<len(sources):v["publisher"]=sources[source_index].get("publisher","SOURCE")
            query=str(v.get("query") or beat["text"])
            must_match=v.get("mustMatch",[])
            if not isinstance(must_match,list):must_match=[]
            allow_reuse=bool(v.get("allowReuse",False))
            src,score=choose_source(source_assets.get(key),query,must_match,used_source_assets,allow_reuse)
            v["matchScore"]=score
            if src:
                v["src"]=src
                if not allow_reuse:used_source_assets.add(src)
            print(f'Source beat {index}: query="{query}" required={must_match} match={score:.3f} src={src or "REJECTED"}')
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
    print("Explain modes:",[b["visual"].get("mode") for b in visual_beats if b["visual"]["type"]=="explain"])
    print("Visual holds:",[round(float(b["end"])-float(b["start"]),2) for b in visual_beats])

if __name__=="__main__":main()
