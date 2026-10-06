#!/usr/bin/env python3
"""Fail closed when a visual plan drifts back to text-heavy template video."""
from __future__ import annotations
import argparse,json,math,re
from pathlib import Path

GENERIC={"fact","kinetic","symbol","text"}
STRONG={"drawn-diagram","source","chart","timeline","metric","comparison"}

def words(value:object)->int:
    return len(re.findall(r"\S+",str(value or "")))

def displayed_words(v:dict)->int:
    kind=v.get("type")
    if kind=="fact":return words(v.get("headline"))+words(v.get("detail"))
    if kind=="kinetic":return words(v.get("text"))
    if kind=="text":return words(v.get("text"))
    if kind=="symbol":return words(v.get("symbol"))
    if kind=="logo":return words(v.get("label"))
    if kind=="drawn-diagram":return sum(words(x) for x in v.get("labels",[]))
    return 0

def audit(props:dict)->dict:
    windows=props.get("visualBeats") or []
    visuals=[b.get("visual") or {} for b in windows]
    kinds=[str(v.get("type","")) for v in visuals]
    sources=[v for v in visuals if v.get("type")=="source"]
    ids=[str(v.get("src") or "") for v in sources]
    hashes=[str(v.get("visualHash") or "") for v in sources]
    problems=[]
    if not windows:problems.append("No visual windows")
    if any(not x for x in ids):problems.append("Source frame missing image")
    if len(ids)!=len(set(ids)):problems.append("Identical source asset repeated")
    for i,a in enumerate(hashes):
        if not a:continue
        for b in hashes[i+1:]:
            if not b:continue
            try:
                if len(a)==len(b)==16 and (int(a,16)^int(b,16)).bit_count()<=3:
                    problems.append("Near-identical source image repeated");break
            except ValueError:pass

    generic_ratio=sum(k in GENERIC for k in kinds)/max(1,len(kinds))
    generic_count=sum(k in GENERIC for k in kinds)
    generic_max=max(2,math.floor(len(windows)*0.20))
    if len(windows)>=8 and generic_count>generic_max:
        problems.append(f"Too many typography/generic scenes: {generic_count}/{len(windows)} (max {generic_max})")
    if any(displayed_words(v)>5 for v in visuals if v.get("type") in GENERIC):
        problems.append("A typography-led scene contains more than five large on-screen words")
    total_large_words=sum(displayed_words(v) for v in visuals if v.get("type") in GENERIC)
    if len(windows)>=8 and total_large_words/max(1,len(windows))>1.25:
        problems.append("Large on-screen word density is too high")

    drawn=[v for v in visuals if v.get("type")=="drawn-diagram"]
    explanation_beats=sum(
        str(b.get("editorialRole","")).lower() in {"explanation","transition"}
        for b in (props.get("beats") or []) if isinstance(b,dict)
    )
    technical=explanation_beats>=2
    if technical and len(windows)>=8:
        minimum=max(2,math.floor(len(windows)*0.32))
        if len(drawn)<minimum:
            problems.append(f"Technical Short needs more drawn diagrams: {len(drawn)}/{len(windows)} (minimum {minimum})")
    strong_ratio=sum(k in STRONG for k in kinds)/max(1,len(kinds))
    if technical and len(windows)>=8 and strong_ratio<0.62:
        problems.append(f"Not enough diagram/source-led scenes: {strong_ratio:.0%} (minimum 62%)")

    if len(windows)>=12 and len(set(kinds))<3:problems.append("Not enough visual treatment variety")
    streak=0
    for kind in kinds:
        streak=streak+1 if kind in GENERIC else 0
        if streak>3:
            problems.append("More than three consecutive typography/generic scenes");break

    patterns=[f"{v.get('mode')}:{v.get('variant',0)}" for v in visuals if v.get("type")=="explain"]
    transitions=0
    for a,b in zip(visuals,visuals[1:]):
        if a.get("type")=="drawn-diagram" and b.get("type")=="drawn-diagram" and a.get("kind")!=b.get("kind"):
            if a.get("continuityKey") and a.get("continuityKey")==b.get("continuityKey") and a.get("transition")!="cut" and b.get("transition")!="cut":
                transitions+=1
            else:problems.append("Adjacent drawn diagrams are missing morph continuity metadata")
    if len(patterns)!=len(set(patterns)):problems.append("Exact legacy diagram layout repeated")

    return {"passed":not problems,"issues":list(dict.fromkeys(problems)),
            "shots":len(windows),"sourceShots":len(ids),"uniqueSourceShots":len(set(ids)),
            "genericFraction":round(generic_ratio,3),"strongVisualFraction":round(strong_ratio,3),
            "largeTextWords":total_large_words,"treatments":kinds,"diagramPatterns":patterns,
            "drawnDiagramCount":len(drawn),"diagramFraction":round(len(drawn)/max(1,len(windows)),3),
            "diagramMorphTransitions":transitions,"explanationBeats":explanation_beats}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--props",default="build/render-props.json")
    p.add_argument("--out",default="build/quality-gate-report.json")
    a=p.parse_args()
    result=audit(json.loads(Path(a.props).read_text(encoding="utf-8")))
    Path(a.out).parent.mkdir(parents=True,exist_ok=True)
    Path(a.out).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("Visual quality gate:",json.dumps(result))
    if not result["passed"]:raise SystemExit("Visual quality gate failed; video will not be published")

if __name__=="__main__":main()
