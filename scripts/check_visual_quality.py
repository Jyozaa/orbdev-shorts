#!/usr/bin/env python3
"""Stop poor visual renders before costly Remotion work and YouTube uploads."""
from __future__ import annotations
import argparse,json
from pathlib import Path

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
                    problems.append("Near-identical source image repeated")
                    break
            except ValueError:pass
    generic={"fact","kinetic","symbol","text"}
    ratio=sum(k in generic for k in kinds)/max(1,len(kinds))
    if len(windows)>=12 and ratio>0.70:problems.append(f"Excessive generic scenes: {ratio:.0%}")
    if len(windows)>=12 and len(set(kinds))<3:problems.append("Not enough visual treatment variety")
    streak=0
    for kind in kinds:
        streak=streak+1 if kind in generic else 0
        if streak>6:
            problems.append("More than six consecutive generic scenes")
            break
    patterns=[f"{v.get('mode')}:{v.get('variant',0)}" for v in visuals if v.get("type")=="explain"]
    if len(patterns)!=len(set(patterns)):problems.append("Exact diagram layout repeated")
    return {"passed":not problems,"issues":list(dict.fromkeys(problems)),
            "shots":len(windows),"sourceShots":len(ids),"uniqueSourceShots":len(set(ids)),
            "genericFraction":round(ratio,3),"treatments":kinds,"diagramPatterns":patterns}

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
