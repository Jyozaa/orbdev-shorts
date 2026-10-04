from __future__ import annotations
import argparse,json
from pathlib import Path
def main():
    p=argparse.ArgumentParser();p.add_argument("--receipts-dir",required=True);p.add_argument("--covered",default="history/covered.json");p.add_argument("--output",required=True);a=p.parse_args()
    covered=json.loads(Path(a.covered).read_text(encoding="utf-8")) if Path(a.covered).exists() else {"version":1,"stories":[]};by={str(x.get("storyKey")):x for x in covered.get("stories",[]) if x.get("storyKey")};receipts=[]
    root=Path(a.receipts_dir)
    for path in root.rglob("*.json") if root.exists() else []:
        try:
            row=json.loads(path.read_text(encoding="utf-8"))
            if row.get("storyKey"):receipts.append(row)
        except Exception:pass
    for r in receipts:
        by[str(r["storyKey"])]={"storyKey":r["storyKey"],"slug":r.get("slug"),"headline":r.get("headline"),"selectedAt":r.get("selectedAt"),"score":r.get("score"),"sourceUrls":r.get("sourceUrls") or [],"renderedAt":r.get("renderedAt"),"youtubeUrl":r.get("youtubeUrl") or None}
    out={"version":1,"stories":list(by.values())};Path(a.output).write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n",encoding="utf-8");print(f"Covered history: {len(receipts)} receipts merged")
if __name__=="__main__":main()
