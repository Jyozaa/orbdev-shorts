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
MAX_IMAGES_PER_SOURCE = 5


def fetch(url: str, timeout: int = 30, referer: str | None = None) -> tuple[bytes, str]:
    headers = {
        "User-Agent": "Mozilla/5.0 orbdev-renderer",
        "Accept": "text/html,application/xhtml+xml,image/avif,image/webp,image/*,*/*;q=0.8",
    }
    if referer:
        headers["Referer"] = referer
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(), response.headers.get("Content-Type", "")


def absolute(base_url: str, value: str) -> str:
    return urllib.parse.urljoin(base_url, html.unescape(value.strip()))


def extract_image_candidates(html_text: str, base_url: str) -> list[str]:
    candidates: list[tuple[int, str]] = []
    seen: set[str] = set()

    def add(raw: str, score: int) -> None:
        if not raw:
            return
        value = raw.strip()
        if value.startswith("data:"):
            return
        url = absolute(base_url, value)
        lowered = url.lower()
        if url in seen:
            return
        if any(term in lowered for term in (
            "avatar", "icon", "favicon", "sprite", "emoji", "tracking",
            "pixel.gif", "logo-small", "author"
        )):
            return
        seen.add(url)
        candidates.append((score, url))

    meta_patterns = [
        (r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']', 120),
        (r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']', 120),
        (r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']', 115),
        (r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image(?::src)?["\']', 115),
    ]
    for pattern, score in meta_patterns:
        for match in re.finditer(pattern, html_text, flags=re.I):
            add(match.group(1), score)

    for tag_match in re.finditer(r"<img\b[^>]*>", html_text, flags=re.I):
        tag = tag_match.group(0)
        lowered = tag.lower()
        score = 50
        if any(term in lowered for term in ("hero", "featured", "article", "content", "media", "gallery")):
            score += 35
        if any(term in lowered for term in ('width="1200', "width='1200", 'width="1920', "width='1920")):
            score += 15

        for attr in ("src", "data-src", "data-lazy-src", "data-original"):
            match = re.search(rf'\b{attr}=["\']([^"\']+)["\']', tag, flags=re.I)
            if match:
                add(match.group(1), score)

        srcset = re.search(r'\bsrcset=["\']([^"\']+)["\']', tag, flags=re.I)
        if srcset:
            parts = [part.strip().split()[0] for part in srcset.group(1).split(",") if part.strip()]
            if parts:
                add(parts[-1], score + 10)

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [url for _, url in candidates]


def normalize_image(source: Path, target: Path) -> bool:
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-loglevel", "error", "-i", str(source),
                "-vf", "scale='min(1400,iw)':-2",
                "-frames:v", "1", "-q:v", "2", str(target)
            ],
            check=True,
        )
        dims = subprocess.check_output(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0:s=x", str(target)
            ],
            text=True,
        ).strip()
        width, height = [int(value) for value in dims.split("x")]
        if width < 480 or height < 260:
            target.unlink(missing_ok=True)
            return False
        return True
    except Exception:
        target.unlink(missing_ok=True)
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


def capture_candidate(url: str, referer: str, index: int, variant: int) -> str | None:
    temp = BUILD / f"source-{index}-{variant}.asset"
    target = PUBLIC / f"source-{index}-{variant}.jpg"
    try:
        image_bytes, content_type = fetch(url, referer=referer)
        if "text/html" in content_type:
            return None
        temp.write_bytes(image_bytes)
        if normalize_image(temp, target):
            return f"sources/{target.name}"
    except Exception as exc:
        print(f"Source {index} image {variant} failed: {exc}")
    finally:
        temp.unlink(missing_ok=True)
    return None


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
    report: dict[str, object] = {}

    for index in requested:
        if index < 0 or index >= len(sources):
            continue
        url = sources[index].get("url")
        if not isinstance(url, str):
            continue

        assets: list[str] = []
        page_text = ""
        try:
            page_bytes, content_type = fetch(url)
            if "text/html" in content_type or page_bytes.lstrip().startswith(b"<"):
                page_text = page_bytes.decode("utf-8", errors="ignore")
                candidates = extract_image_candidates(page_text, url)
                for candidate in candidates:
                    if len(assets) >= MAX_IMAGES_PER_SOURCE:
                        break
                    captured = capture_candidate(candidate, url, index, len(assets))
                    if captured and captured not in assets:
                        assets.append(captured)
            else:
                temp = BUILD / f"source-{index}-direct.asset"
                target = PUBLIC / f"source-{index}-0.jpg"
                temp.write_bytes(page_bytes)
                if normalize_image(temp, target):
                    assets.append(f"sources/{target.name}")
                temp.unlink(missing_ok=True)
        except Exception as exc:
            print(f"Source {index}: page/image discovery failed: {exc}")

        if not assets:
            screenshot = PUBLIC / f"source-{index}-page.png"
            if chrome_screenshot(url, screenshot):
                assets.append(f"sources/{screenshot.name}")
                print(f"Source {index}: using page screenshot fallback")

        report[str(index)] = {
            "assets": assets,
            "count": len(assets),
        }
        print(f"Source {index}: captured {len(assets)} official/source image assets")

    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
