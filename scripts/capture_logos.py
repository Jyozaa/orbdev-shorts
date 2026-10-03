from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

BUILD = Path("build")
PUBLIC = Path("public/logos")
REPORT = BUILD / "logo-assets.json"


def safe_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9-]+", "-", value.lower()).strip("-")


def collect(story: dict[str, object]) -> set[str]:
    slugs: set[str] = set()
    for beat in story.get("beats", []):
        visual = beat.get("visual", {})
        if visual.get("type") == "logo":
            slug = visual.get("slug")
            if isinstance(slug, str) and slug.strip():
                slugs.add(safe_slug(slug))
        elif visual.get("type") == "flow":
            for node in visual.get("nodes", []):
                if isinstance(node, dict) and node.get("kind") == "logo":
                    slug = node.get("slug")
                    if isinstance(slug, str) and slug.strip():
                        slugs.add(safe_slug(slug))
    return slugs


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: capture_logos.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    PUBLIC.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    report: dict[str, str] = {}

    for slug in sorted(collect(story)):
        target = PUBLIC / f"{slug}.svg"
        url = f"https://cdn.simpleicons.org/{slug}/ffffff"
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "orbdev-renderer",
                    "Accept": "image/svg+xml,image/*,*/*;q=0.8",
                },
            )
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read()
            if b"<svg" not in data[:500].lower():
                raise ValueError("response was not SVG")
            target.write_bytes(data)
            report[slug] = f"logos/{target.name}"
            print(f"Logo {slug}: captured")
        except Exception as exc:
            print(f"Logo {slug}: unavailable: {exc}")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
