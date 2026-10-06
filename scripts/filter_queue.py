#!/usr/bin/env python3
"""Select only one unpublished story per underlying event."""
from __future__ import annotations
import argparse,glob,json,sys
from pathlib import Path
from story_identity import duplicate

def load(path:Path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError):return None

def filter_paths(requested:list[str],all_files:list[str],covered:list[dict])->list[str]:
    catalog={path:load(Path(path)) for path in sorted(set(all_files))}
    chosen=[]
    for path in sorted(set(requested)):
        story=catalog.get(path)
        if not isinstance(story,dict):continue
        if any(duplicate(story,row) for row in covered):
            print(f"Skip published event: {path}",file=sys.stderr)
            continue
        prior=next((other for other,s in catalog.items()
                    if other<path and isinstance(s,dict) and duplicate(story,s)),None)
        if prior:
            print(f"Skip queue duplicate: {path} (same event as {prior})",file=sys.stderr)
            continue
        chosen.append(path)
    return chosen

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--covered",default="history/covered.json")
    p.add_argument("files",nargs="*")
    a=p.parse_args()
    state=load(Path(a.covered)) or {}
    print(json.dumps(filter_paths(a.files,glob.glob("stories/queue/*.json"),state.get("stories",[])),separators=(",",":")))

if __name__=="__main__":main()
