"""Merge production receipts without overwriting another video on the same topic."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def receipt_identity(row: dict) -> str:
    if row.get("youtubeVideoId"):
        return "youtube:" + str(row["youtubeVideoId"])
    if row.get("videoSha256"):
        return "mp4:" + str(row["videoSha256"])
    if row.get("storyPlanSha256"):
        return "plan:" + str(row["storyPlanSha256"])
    # Legacy render receipts have no video hashes. Preserve separately by slug.
    return "legacy:" + str(row.get("storyKey") or "") + ":" + str(row.get("slug") or "")


def merge_receipts(previous: list[dict], receipts: list[dict]) -> list[dict]:
    by = {receipt_identity(row): dict(row) for row in previous}
    for row in receipts:
        if not row.get("storyKey") and not row.get("slug"):
            continue
        key = receipt_identity(row)
        original = by.get(key, {})
        # Do not let stale receipts erase fields collected by later jobs.
        by[key] = {**original, **{k: v for k, v in row.items() if v is not None}}
    return list(by.values())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipts-dir", required=True)
    parser.add_argument("--covered", default="history/covered.json")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    path = Path(args.covered)
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"version": 1, "stories": []}
    receipts = []
    root = Path(args.receipts_dir)
    for file in root.rglob("*.json") if root.exists() else []:
        try:
            row = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(row, dict):
                receipts.append(row)
        except (OSError, ValueError):
            continue
    merged = merge_receipts(existing.get("stories", []), receipts)
    Path(args.output).write_text(
        json.dumps({"version": 1, "stories": merged}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Covered history: {len(receipts)} receipts merged; {len(merged)} distinct attempts/videos retained")


if __name__ == "__main__":
    main()
