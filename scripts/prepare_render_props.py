from __future__ import annotations
import copy,hashlib,json,math,re,sys,unicodedata
from pathlib import Path

BUILD_DIR=Path("build"); CAPTIONS_PATH=Path("public/captions.json"); MEME_SELECTION_PATH=BUILD_DIR/"meme-selection.json"
SOURCE_ASSETS_PATH=BUILD_DIR/"source-assets.json"; LOGO_ASSETS_PATH=BUILD_DIR/"logo-assets.json"; CUTAWAYS_PATH=BUILD_DIR/"cutaways.json"
MIN_VISUAL_SECONDS=1.05; TARGET_VISUAL_SECONDS=1.55; MAX_VISUAL_SECONDS=2.45
RHYTHM_BREAK_ROLES={"analogy","joke","reaction","punchline","callback"}
SOURCE_MIN_MATCH=0.34
SFX_DURATIONS={"whoosh":.34,"impact":.42,"scratch":.48,"tick":.10}
STOP={"the","a","an","and","or","to","for","of","in","on","with","is","are","was","were","it","this","that","from","your","our","their","just","new","image","images","game","gameplay","hardware","console","quality","comparison","detail","official","article"}
LABEL_STOP=STOP|{"about","after","before","being","can","could","does","doing","even","every","gets","into","more","most","much","only","other","over","same","some","than","then","there","these","they","through","under","using","very","when","where","which","while","will","would"}
DIAGRAM_FIRST_ROLES={"explanation","transition"}
LEGACY_DIAGRAM_TYPES={"explain","diagram","flow","network","comparison"}

def fold_ascii(t:str)->str:
    return unicodedata.normalize("NFKD",t).encode("ascii","ignore").decode("ascii")

def norm(t:str)->str:return re.sub(r"[^a-z0-9]+","",fold_ascii(t).lower())
def tokens(t:str)->set[str]:
    return {x for x in re.sub(r"[^a-z0-9]+"," ",fold_ascii(t).lower()).split() if len(x)>1 and x not in STOP}
def beat_tokens(t:str)->list[str]:return [x for x in (norm(v) for v in re.findall(r"\S+",t)) if x]

def compact_label(value:object)->str:
    words=re.findall(r"[A-Za-z0-9$%+.-]+",str(value or ""))
    words=[w for w in words if w.lower() not in LABEL_STOP]
    return " ".join(words[:2])[:22].strip().upper()

def visual_label_candidates(visual:dict)->list[str]:
    raw=[]
    for key in ("labels","stages","nodes","symbols"):
        value=visual.get(key)
        if isinstance(value,list):raw.extend(value)
    for key in ("center","left","right","headline","text"):
        value=visual.get(key)
        if isinstance(value,str):raw.append(value)
    if visual.get("type")=="flow":
        for node in visual.get("nodes",[]):
            if isinstance(node,dict):raw.append(node.get("label") or node.get("value") or "")
    labels=[];seen=set()
    for value in raw:
        label=compact_label(value)
        if label and label not in seen:
            labels.append(label);seen.add(label)
    return labels

def narration_labels(text:str,limit:int=4)->list[str]:
    raw=re.findall(r"[A-Za-z0-9$%+.-]+",str(text))
    labels=[];seen=set()
    for token in raw:
        if token.lower() in LABEL_STOP or len(token)<2:continue
        label=compact_label(token)
        if label and label not in seen:
            labels.append(label);seen.add(label)
        if len(labels)>=limit:break
    return labels

def diagram_kind_for_beat(beat:dict,position:int=0)->str:
    visual=beat.get("visual",{});kind=str(visual.get("type",""))
    mode=str(visual.get("mode",""))
    if kind=="comparison" or mode in {"pixel-upscale","stability"}:return "comparison"
    if kind=="network" or mode=="network-shrink":return "mesh"
    if kind in {"flow","diagram"} or mode=="pipeline":return "flow"
    if mode=="fanout":return "branch"
    if mode=="capacity":return "stack"
    text=(" ".join([str(beat.get("text","")),json.dumps(visual,ensure_ascii=False)])).lower()
    # Specific mechanism terms outrank generic temporal words such as "before".
    rules=[
        ("shield",{"security","secure","breach","protect","protected","firewall","sandbox"}),
        ("wave",{"audio","voice","speech","sound","signal","wave","frequency","radio"}),
        ("branch",{"branch","split","route","router","choice","choose","expert","specialist","dispatch"}),
        ("stack",{"layer","stack","cache","memory","context","storage","buffer"}),
        ("mesh",{"network","graph","peer","node","connected","connection","cluster"}),
        ("orbit",{"agent","agents","tool","tools","ecosystem","plugin","plugins","service","services"}),
        ("funnel",{"filter","merge","combine","aggregate","select","compress","reduce","narrow"}),
        ("comparison",{"versus"," vs ","compare","compared","instead","old","newer","difference"}),
        ("growth",{"grow","growth","increase","decrease","faster","slower","speed","performance","benchmark","scale","billion","million","percent","%"}),
        ("timeline",{"timeline","first","later","eventually","before","after","then","now","year","month","week","day"}),
        ("flow",{"input","output","process","pipeline","token","tokens","request","requests","data","through"}),
    ]
    padded=f" {text} "
    for candidate,terms in rules:
        if any(term in padded for term in terms):return candidate
    fallbacks=["flow","branch","orbit","stack","mesh"]
    seed=int(hashlib.sha1(f"{position}|{beat.get('text','')}".encode()).hexdigest()[:8],16)
    return fallbacks[seed%len(fallbacks)]

def drawn_diagram_from_beat(beat:dict,position:int=0,previous_kind:str|None=None)->dict:
    visual=beat.get("visual",{}) if isinstance(beat.get("visual"),dict) else {}
    kind=diagram_kind_for_beat(beat,position)
    alternates={
        "flow":["branch","stack"],"branch":["orbit","mesh"],"orbit":["mesh","branch"],
        "mesh":["orbit","flow"],"growth":["comparison","timeline"],"comparison":["growth","flow"],
        "shield":["mesh","flow"],"stack":["flow","funnel"],"timeline":["growth","flow"],
        "wave":["flow","orbit"],"funnel":["flow","stack"],
    }
    if previous_kind==kind:
        kind=alternates.get(kind,["flow"])[position%len(alternates.get(kind,["flow"]))]
    target={"comparison":2,"growth":2,"wave":2,"shield":1,"mesh":2,"flow":3,
            "branch":3,"orbit":4,"stack":4,"timeline":3,"funnel":4}.get(kind,3)
    labels=visual_label_candidates(visual)
    for label in narration_labels(str(beat.get("text","")),target):
        if label not in labels:labels.append(label)
    labels=labels[:target]
    seed=int(hashlib.sha256(f"{position}|{kind}|{beat.get('text','')}".encode()).hexdigest()[:8],16)
    result={"type":"drawn-diagram","kind":kind,"variant":seed%4}
    if labels:result["labels"]=labels
    if kind=="mesh":result["focus"]=seed%6
    return result

def should_upgrade_to_drawn(beat:dict,position:int)->bool:
    visual=beat.get("visual",{});kind=str(visual.get("type",""));role=str(beat.get("editorialRole","")).lower()
    if kind=="drawn-diagram" or kind in {"source","logo","metric","chart","timeline"}:return False
    if role in RHYTHM_BREAK_ROLES:return False
    if kind in LEGACY_DIAGRAM_TYPES:return True
    word_count=len(re.findall(r"\S+",str(beat.get("text",""))))
    if role in DIAGRAM_FIRST_ROLES:return True
    if position>0 and role in {"fact","setup"} and kind in {"fact","text","kinetic","symbol"} and word_count>=5:return True
    return False

def apply_diagram_first(beats:list[dict])->int:
    converted=0;previous_kind=None
    for position,beat in enumerate(beats):
        visual=beat.get("visual",{})
        if visual.get("type")=="source" and visual.get("src"):
            previous_kind=None;continue
        rejected_source=visual.get("type")=="source" and not visual.get("src")
        if rejected_source or should_upgrade_to_drawn(beat,position):
            role=str(beat.get("editorialRole","")).lower()
            if role not in RHYTHM_BREAK_ROLES:
                beat["visual"]=drawn_diagram_from_beat(beat,position,previous_kind)
                previous_kind=str(beat["visual"]["kind"]);converted+=1;continue
        if beat.get("visual",{}).get("type")=="drawn-diagram":
            previous_kind=str(beat["visual"].get("kind",""))
        else:previous_kind=None
    return converted

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

def perceptually_same(a:str,b:str)->bool:
    """dHash: tolerate slight source-image re-encodes, never count them as fresh media."""
    if len(a)!=16 or len(b)!=16:return bool(a and a==b)
    try:return (int(a,16)^int(b,16)).bit_count()<=3
    except ValueError:return False

def choose_source(entry:object,query:str,must_match:list[str],used:set[str],allow_reuse:bool=False,used_hashes:list[str]|None=None):
    # Old queued stories may still specify allowReuse=true. Never reuse an actual
    # image inside the same Short: a re-crop is not a new shot.
    if isinstance(entry,str):
        return (None,0.0) if entry in used else ({"src":entry},0.35)
    if not isinstance(entry,dict):return None,0.0
    assets=entry.get("assets",[])
    if not isinstance(assets,list):return None,0.0
    required=[norm(v) for v in must_match if isinstance(v,str) and norm(v)]
    scored=[]
    for asset in assets:
        if not isinstance(asset,dict):continue
        src=str(asset.get("src",""))
        digest=str(asset.get("visualHash") or "")
        if not src or src in used:continue
        if digest and any(perceptually_same(digest,seen) for seen in (used_hashes or [])):continue
        searchable=norm(f'{asset.get("text","")} {asset.get("url","")}')
        if required and not all(term in searchable for term in required):continue
        scored.append((source_match(asset,query),int(asset.get("baseScore",0)),asset))
    scored.sort(key=lambda x:(x[0],x[1]),reverse=True)
    if not scored or scored[0][0]<SOURCE_MIN_MATCH:return None,(scored[0][0] if scored else 0.0)
    return scored[0][2],scored[0][0]

ABSTRACT_TYPES={"explain","chart","timeline","comparison","flow","diagram","network","drawn-diagram"}

def family(kind:str)->str:
    if kind in ABSTRACT_TYPES:return "abstract-tech"
    if kind=="source":return "source"
    if kind=="logo":return "brand"
    if kind=="metric":return "metric"
    if kind=="kinetic":return "kinetic"
    return "minimal"

def base_visual_weight(beat)->float:
    v=beat.get("visual",{}); kind=str(v.get("type","text"))
    base={
        "explain":9.0,
        "drawn-diagram":11.4,
        "source":10.8,
        "comparison":8.4,
        "chart":8.1,
        "timeline":7.9,
        "logo":5.8,
        "metric":7.1,
        "network":6.0,
        "flow":5.6,
        "diagram":5.4,
        "kinetic":8.0,
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
        if fam!=prev_family:score+=1.0
        elif fam=="source":score-=0.5
        else:score-=3.0
    role=str(beat.get("editorialRole","")).lower()
    if kind=="drawn-diagram" and role in {"explanation","transition"}:score+=2.0
    if kind=="explain":
        mode=str(v.get("mode",""))
        if prev_explain_mode and mode==prev_explain_mode:
            score-=3.0
    return score

def kinetic_from_beat(beat,position:int=0):
    """Last-resort punctuation only; explanatory fallback is handled by diagrams."""
    words=re.findall(r"[A-Za-z0-9'’.-]+",str(beat.get("text","")))
    compact=" ".join(words[:4]).strip() or "TECH UPDATE"
    emphasis=words[min(len(words),4)-1] if words else "UPDATE"
    return {"type":"kinetic","text":compact,"emphasis":emphasis}

def choose_window_candidate(beats,candidates,prev_family,prev_kind,prev_drawn_kind,prev_explain_mode,explain_count,max_explain,abstract_count,max_abstract,used_explain_modes,logo_count,max_logo):
    viable=[i for i in candidates if base_visual_weight(beats[i])>=0]
    if not viable:
        chosen=max(candidates,key=lambda i:(float(beats[i]["end"])-float(beats[i]["start"]),-i))
        return chosen,True
    non_abstract=[i for i in viable if str(beats[i].get("visual",{}).get("type","")) not in ABSTRACT_TYPES]
    continuity_candidates=[
        i for i in viable
        if prev_kind=="drawn-diagram"
        and str(beats[i].get("visual",{}).get("type",""))=="drawn-diagram"
        and str(beats[i].get("visual",{}).get("kind",""))!=prev_drawn_kind
    ]
    abstract_budget_full=abstract_count>=max_abstract
    if abstract_budget_full and non_abstract:
        viable=non_abstract
    elif prev_family=="abstract-tech":
        allowed=continuity_candidates+non_abstract
        if allowed:viable=allowed
    hard_no_logo=prev_family=="brand" or logo_count>=max_logo
    if hard_no_logo:
        allowed=[i for i in viable if str(beats[i].get("visual",{}).get("type",""))!="logo"]
        if allowed:viable=allowed
    if explain_count>=max_explain:
        allowed=[i for i in viable if str(beats[i].get("visual",{}).get("type",""))!="explain"]
        if allowed:viable=allowed
    if used_explain_modes:
        fresh=[i for i in viable if not(str(beats[i].get("visual",{}).get("type",""))=="explain" and str(beats[i].get("visual",{}).get("mode","")) in used_explain_modes)]
        if fresh:viable=fresh
    chosen=max(viable,key=lambda i:(candidate_score(beats[i],prev_family,prev_explain_mode),float(beats[i]["end"])-float(beats[i]["start"]),-i))
    chosen_visual=beats[chosen].get("visual",{});chosen_kind=str(chosen_visual.get("type",""));chosen_mode=str(chosen_visual.get("mode","")) if chosen_kind=="explain" else ""
    is_drawn_continuation=(prev_kind=="drawn-diagram" and chosen_kind=="drawn-diagram" and str(chosen_visual.get("kind",""))!=prev_drawn_kind)
    force_kinetic=((chosen_kind in ABSTRACT_TYPES and abstract_budget_full) or (prev_family=="abstract-tech" and chosen_kind in ABSTRACT_TYPES and not is_drawn_continuation) or (chosen_kind=="explain" and explain_count>=max_explain) or (chosen_kind=="explain" and chosen_mode in used_explain_modes) or (chosen_kind=="logo" and hard_no_logo))
    return chosen,force_kinetic

def apply_diagram_continuity(windows):
    group=0;i=0
    while i<len(windows)-1:
        left=windows[i].get("visual",{});right=windows[i+1].get("visual",{})
        if left.get("type")=="drawn-diagram" and right.get("type")=="drawn-diagram" and left.get("kind")!=right.get("kind"):
            key=str(left.get("continuityKey") or right.get("continuityKey") or f"diagram-run-{group}")
            left["continuityKey"]=key;right["continuityKey"]=key
            left["continuityOut"]=True;right["continuityIn"]=True
            left.setdefault("transition","morph");right.setdefault("transition","morph")
            j=i+1
            while j+1<len(windows):
                a=windows[j].get("visual",{});b=windows[j+1].get("visual",{})
                if a.get("type")!="drawn-diagram" or b.get("type")!="drawn-diagram" or a.get("kind")==b.get("kind"):break
                a["continuityKey"]=key;b["continuityKey"]=key
                a["continuityOut"]=True;b["continuityIn"]=True
                a.setdefault("transition","morph");b.setdefault("transition","morph")
                j+=1
            group+=1;i=j
        i+=1

def assert_visual_window_diversity(windows,max_explain,max_abstract,max_logo):
    kinds=[str(w.get("visual",{}).get("type","")) for w in windows]
    abstract=sum(1 for kind in kinds if kind in ABSTRACT_TYPES);logos=kinds.count("logo")
    explains=[w for w in windows if str(w.get("visual",{}).get("type",""))=="explain"];modes=[str(w.get("visual",{}).get("mode","")) for w in explains]
    if abstract>max_abstract:raise RuntimeError(f"abstract-tech hard cap exceeded: {abstract}>{max_abstract}")
    if logos>max_logo:raise RuntimeError(f"pure-logo hard cap exceeded: {logos}>{max_logo}")
    if len(explains)>max_explain:raise RuntimeError(f"explain hard cap exceeded: {len(explains)}>{max_explain}")
    if len(modes)!=len(set(modes)):raise RuntimeError(f"repeated explain mode survived selection: {modes}")
    for i in range(len(kinds)-1):
        if kinds[i] in ABSTRACT_TYPES and kinds[i+1] in ABSTRACT_TYPES:
            a=windows[i].get("visual",{});b=windows[i+1].get("visual",{})
            continuous=(a.get("type")=="drawn-diagram" and b.get("type")=="drawn-diagram" and a.get("kind")!=b.get("kind") and a.get("continuityKey") and a.get("continuityKey")==b.get("continuityKey"))
            if not continuous:raise RuntimeError(f"back-to-back abstract-tech windows survived selection at {i}/{i+1}")
        if kinds[i]=="logo" and kinds[i+1]=="logo":raise RuntimeError(f"back-to-back pure-logo windows survived selection at {i}/{i+1}")

def build_visual_windows(beats,cutaway_by_beat,final_duration):
    windows=[];index=0;prev_family=None;prev_kind=None;prev_drawn_kind=None;prev_explain_mode=None;explain_count=0;abstract_count=0;logo_count=0;used_explain_modes:set[str]=set()
    max_explain=max(1,min(2,math.floor(final_duration/16.0)))
    # Phase 4 target: diagrams may lead the visual explanation while source
    # media and memes remain the grounding/punctuation layers.
    max_abstract=max(5,min(12,math.ceil(final_duration/3.2)))
    max_logo=max(1,min(2,math.ceil(final_duration/20.0)))
    while index<len(beats):
        start_index=index;end_index=index;start=float(beats[index]["start"]);end=float(beats[index]["end"])
        while end_index+1<len(beats):
            if end_index in cutaway_by_beat:break
            current=end-start
            current_role=str(beats[end_index].get("editorialRole","")).lower()
            next_role=str(beats[end_index+1].get("editorialRole","")).lower()
            # Fireship-like rhythm: jokes/reactions get their own visual punctuation,
            # and the first five seconds establish energy with denser cuts.
            if current_role in RHYTHM_BREAK_ROLES or next_role in RHYTHM_BREAK_ROLES:break
            if start<5.0 and current>=0.85:break
            if current>=TARGET_VISUAL_SECONDS:break
            next_end=float(beats[end_index+1]["end"])
            if next_end-start>MAX_VISUAL_SECONDS and current>=MIN_VISUAL_SECONDS:break
            end_index+=1;end=next_end
            if end_index in cutaway_by_beat or end-start>=TARGET_VISUAL_SECONDS:break
        candidates=list(range(start_index,end_index+1))
        chosen,force_kinetic=choose_window_candidate(beats,candidates,prev_family,prev_kind,prev_drawn_kind,prev_explain_mode,explain_count,max_explain,abstract_count,max_abstract,used_explain_modes,logo_count,max_logo)
        vb=copy.deepcopy(beats[chosen]);vb["start"]=round(start,4);vb["end"]=round(end,4);vb.pop("meme",None);vb.pop("memeIntent",None);vb.pop("sfx",None)
        if force_kinetic:vb["visual"]=kinetic_from_beat(beats[chosen],chosen)
        windows.append(vb);kind=str(vb.get("visual",{}).get("type","text"));prev_family=family(kind);prev_kind=kind
        prev_drawn_kind=str(vb.get("visual",{}).get("kind","")) if kind=="drawn-diagram" else None
        if kind in ABSTRACT_TYPES:abstract_count+=1
        if kind=="logo":logo_count+=1
        if kind=="explain":
            explain_count+=1;prev_explain_mode=str(vb.get("visual",{}).get("mode",""));used_explain_modes.add(prev_explain_mode)
        else:prev_explain_mode=None
        index=end_index+1
    if windows and float(windows[-1]["end"])<final_duration:windows[-1]["end"]=round(final_duration,4)
    apply_diagram_continuity(windows)
    assert_visual_window_diversity(windows,max_explain,max_abstract,max_logo)
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
    prepared=[];cursor=0;used_source_assets:set[str]=set();used_source_hashes:list[str]=[]
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
            asset,score=choose_source(source_assets.get(key),query,must_match,used_source_assets,allow_reuse,used_source_hashes)
            v["matchScore"]=score
            src=str(asset.get("src","")) if isinstance(asset,dict) else ""
            if src:
                v["src"]=src;width=int(asset.get("width",0) or 0);height=int(asset.get("height",0) or 0)
                if width>0 and height>0:
                    ratio=width/height;v["assetWidth"]=width;v["assetHeight"]=height;v["layout"]="landscape" if ratio>=1.15 else ("portrait" if ratio<=0.78 else "square")
                else:v["layout"]="unknown"
                used_source_assets.add(src)
                if asset.get("visualHash"):used_source_hashes.append(str(asset["visualHash"]))
                v["visualHash"]=asset.get("visualHash")
            print(f'Source beat {index}: query="{query}" required={must_match} match={score:.3f} src={src or "REJECTED"} layout={v.get("layout","none")}')
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

    upgraded=apply_diagram_first(prepared)
    print(f"Diagram-first upgrades: {upgraded}/{len(prepared)} semantic beats")
    visual_beats=build_visual_windows(prepared,cutaway_by_beat,final_duration)
    # Assign a reproducible, story-specific geometry rather than the same pipeline
    # or fanout in every video. Rotate away from recent layouts where possible.
    history_path=Path("history/visual-history.json")
    visual_history=json.loads(history_path.read_text(encoding="utf-8")) if history_path.exists() else {"stories":[]}
    recent=visual_history.get("stories",[])[-24:]
    local_patterns:set[str]=set()
    for i,beat in enumerate(visual_beats):
        visual=beat.get("visual",{})
        if visual.get("type")=="explain":
            mode=str(visual.get("mode","fanout"))
            seed=int(hashlib.sha256(f"{story.get('slug','')}|{mode}|{i}".encode()).hexdigest()[:8],16)
            def pattern_cost(variant:int)->tuple[int,int,int]:
                pattern=f"legacy:{mode}:{variant}"
                return (
                    100 if pattern in local_patterns else 0,
                    sum(1 for item in recent for token in item.get("patterns",[]) if token==pattern),
                    (variant-seed)%6,
                )
            variant=min(range(6),key=pattern_cost)
            visual["variant"]=variant
            local_patterns.add(f"legacy:{mode}:{variant}")
        elif visual.get("type")=="drawn-diagram":
            kind=str(visual.get("kind","flow"))
            seed=int(hashlib.sha256(f"{story.get('slug','')}|drawn|{kind}|{i}".encode()).hexdigest()[:8],16)
            def drawn_cost(variant:int)->tuple[int,int,int]:
                pattern=f"drawn:{kind}:{variant}"
                return (
                    100 if pattern in local_patterns else 0,
                    sum(1 for item in recent for token in item.get("patterns",[]) if token==pattern),
                    (variant-seed)%4,
                )
            variant=min(range(4),key=drawn_cost)
            visual["variant"]=variant
            local_patterns.add(f"drawn:{kind}:{variant}")
    props=dict(story);props["durationSeconds"]=round(final_duration,4);props["beats"]=prepared;props["visualBeats"]=visual_beats;props["captions"]=words;props["cutaways"]=cutaways
    BUILD_DIR.mkdir(parents=True,exist_ok=True);(BUILD_DIR/"render-props.json").write_text(json.dumps(props,indent=2),encoding="utf-8")
    (BUILD_DIR/"visual-quality.json").write_text(json.dumps({"slug":story.get("slug"),"patterns":sorted(local_patterns)},indent=2),encoding="utf-8")
    print(f"Render props ready: {len(prepared)} semantic beats -> {len(visual_beats)} visual windows, {final_duration:.2f}s")
    treatments=[b["visual"]["type"] for b in visual_beats]
    print("Visual treatments:",treatments)
    print("Explain modes:",[b["visual"].get("mode") for b in visual_beats if b["visual"]["type"]=="explain"])
    abstract=sum(1 for kind in treatments if kind in ABSTRACT_TYPES)
    drawn=treatments.count("drawn-diagram")
    print(f"Diagram/abstract windows: {abstract}/{len(treatments)} ({abstract/max(1,len(treatments)):.0%}); drawn diagrams: {drawn}")
    source_count=treatments.count("source");logo_count=treatments.count("logo")
    print(f"Real-source windows: {source_count}/{len(treatments)} ({source_count/max(1,len(treatments)):.0%}); pure logos: {logo_count}")
    print("Visual holds:",[round(float(b["end"])-float(b["start"]),2) for b in visual_beats])

if __name__=="__main__":main()
