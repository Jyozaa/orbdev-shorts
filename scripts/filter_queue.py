#!/usr/bin/env python3
"""Only suppress identical storyboards; repeat coverage/angles are welcome."""
from __future__ import annotations
import argparse
import glob
import json
import sys
from pathlib import Path
from story_identity import story_plan_sha256


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def filter_paths(requested: list[str], all_files: list[str], covered: list[dict]) -> list[str]:
    catalog = {path: load(Path(path)) for path in sorted(set(all_files))}
    published_plans = {
        str(row.get("storyPlanSha256")).lower()
        for row in covered if row.get("youtubeVideoId") and row.get("storyPlanSha256")
    }
    # Legacy receipts lacking a plan fingerprint cannot establish a duplicate.
    seen_plans: set[str] = set()
    chosen = []
    for path in sorted(set(requested)):
        story = catalog.get(path)
        if not isinstance(story, dict):
            continue
        plan = story_plan_sha256(story)
        if plan and plan in published_plans:
            print(f"Skipping previously published identical storyboard: {path}",
                  file=sys.stderr)
            continue
        if plan and plan in seen_plans:
            print(f"Skipping second copy of same storyboard in this batch: {path}",
                  file=sys.stderr)
            continue
        if plan:
            seen_plans.add(plan)
        chosen.append(path)
    return chosen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--covered", default="history/covered.json")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    state = load(Path(args.covered)) or {}
    print(json.dumps(filter_paths(args.files, glob.glob("stories/queue/*.json"),
                                  state.get("stories", [])), separators=(",", ":")))


if __name__ == "__main__":
    main()
