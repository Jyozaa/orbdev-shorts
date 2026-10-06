#!/usr/bin/env python3
"""Append successful render diagram variants, merging fresh state from main."""
from __future__ import annotations
import argparse,json
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--receipts-dir",required=True)
    p.add_argument("--history",default="history/visual-history.json")
    p.add_argument("--output",required=True)
    a=p.parse_args()
    existing=Path(a.history)
    data=json.loads(existing.read_text(encoding="utf-8")) if existing.exists() else {"version":1,"stories":[]}
    by={str(r["slug"]):r for r in data.get("stories",[]) if r.get("slug")}
    for path in sorted(Path(a.receipts_dir).rglob("*.json")):
        try:receipt=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError):continue
        slug=str(receipt.get("slug") or "")
        if not slug:continue
        patterns=receipt.get("visualPatterns") or []
        if not isinstance(patterns,list) or not patterns:continue
        by[slug]={"slug":slug,"patterns":sorted(set(str(x) for x in patterns)), "renderedAt":receipt.get("renderedAt")}
    ordered=sorted(by.values(),key=lambda r:str(r.get("renderedAt") or ""))[-120:]
    Path(a.output).write_text(json.dumps({"version":1,"stories":ordered},indent=2)+"\n",encoding="utf-8")
    print("Visual history:",len(ordered),"stories")

if __name__=="__main__":main()
