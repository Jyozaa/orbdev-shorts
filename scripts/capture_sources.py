from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BUILD = Path("build")
PUBLIC = Path("public/sources")
REPORT = BUILD / "source-assets.json"


def fetch(url: str, timeout: int = 30) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 orbdev-renderer",
            "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def og_image(html_text: str, base_url: str) -> str | None:
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
    ]
    for pattern in patterns:
        match = re.search(pattern, html_text, flags=re.I)
        if match:
            return urllib.parse.urljoin(base_url, html.unescape(match.group(1)))
    return None


def normalize_image(source: Path, target: Path) -> bool:
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-vf", "scale=960:-2:force_original_aspect_ratio=decrease",
                "-frames:v", "1", str(target)
            ],
            check=True,
        )
        return True
    except Exception:
        return False


def chrome_screenshot(url: str, target: Path) -> bool:
    chrome = next(
        (candidate for candidate in (
            shutil.which("google-chrome"),
            shutil.which("google-chrome-stable"),
            shutil.which("chromium"),
            shutil.which("chromium-browser"),
        ) if candidate),
        None,
    )
    if not chrome:
        return False

    try:
        subprocess.run(
            [
                chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
                "--hide-scrollbars", "--window-size=1080,1400",
                "--virtual-time-budget=3500",
                f"--screenshot={target.resolve()}", url
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=25,
        )
        return target.exists()
    except Exception:
        return False


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: capture_sources.py <story.json>")

    story = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    sources = story.get("editorial", {}).get("sources", [])
    requested = sorted({
        int(beat["visual"]["sourceIndex"])
        for beat in story.get("beats", [])
        if beat.get("visual", {}).get("type") == "source"
    })

    PUBLIC.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(parents=True, exist_ok=True)
    report: dict[str, str] = {}

    for index in requested:
        if index < 0 or index >= len(sources):
            continue
        url = sources[index].get("url")
        if not isinstance(url, str):
            continue

        target = PUBLIC / f"source-{index}.jpg"
        temp = BUILD / f"source-{index}.asset"

        try:
            page_bytes, content_type = fetch(url)
            if "text/html" in content_type or page_bytes.lstrip().startswith(b"<"):
                page_text = page_bytes.decode("utf-8", errors="ignore")
                image_url = og_image(page_text, url)
                if image_url:
                    image_bytes, _ = fetch(image_url)
                    temp.write_bytes(image_bytes)
                    if normalize_image(temp, target):
                        report[str(index)] = f"sources/{target.name}"
                        print(f"Source {index}: captured OpenGraph image")
                        continue
            else:
                temp.write_bytes(page_bytes)
                if normalize_image(temp, target):
                    report[str(index)] = f"sources/{target.name}"
                    print(f"Source {index}: captured direct image")
                    continue
        except Exception as exc:
            print(f"Source {index}: image fetch failed: {exc}")
        finally:
            temp.unlink(missing_ok=True)

        screenshot = PUBLIC / f"source-{index}.png"
        if chrome_screenshot(url, screenshot):
            report[str(index)] = f"sources/{screenshot.name}"
            print(f"Source {index}: captured page screenshot")
        else:
            print(f"Source {index}: no visual asset available")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
