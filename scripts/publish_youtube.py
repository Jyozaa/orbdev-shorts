from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"missing required environment variable: {name}")
    return value


def normalized_hashtags(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value).strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = "#" + tag.replace(" ", "")
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tag)
    return out[:5]


def primary_source_urls(story: dict[str, object]) -> list[str]:
    editorial = story.get("editorial")
    if not isinstance(editorial, dict):
        return []
    sources = editorial.get("sources")
    if not isinstance(sources, list):
        return []
    urls: list[str] = []
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or source.get("primary") is not True:
            continue
        url = str(source.get("url") or "").strip()
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return urls


def build_description(story: dict[str, object], publish: dict[str, object]) -> str:
    base = str(publish.get("description") or "").strip()
    source_urls = primary_source_urls(story)
    hashtags = normalized_hashtags(publish.get("hashtags"))

    sections: list[str] = []
    if base:
        sections.append(base)

    missing_sources = [url for url in source_urls if url not in base]
    if missing_sources:
        sections.append("Sources:\n" + "\n".join(missing_sources))

    if hashtags:
        hashtag_line = " ".join(hashtags)
        if not all(tag.lower() in base.lower() for tag in hashtags):
            sections.append(hashtag_line)

    return "\n\n".join(section for section in sections if section).strip()[:5000]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: publish_youtube.py <story.json> <video.mp4>")

    story_path = Path(sys.argv[1])
    video_path = Path(sys.argv[2])
    if not story_path.exists() or not video_path.exists():
        raise SystemExit("story or video file does not exist")

    story = json.loads(story_path.read_text(encoding="utf-8"))
    publish = story.get("publish") or {}
    title = str(publish.get("youtubeTitle") or story.get("title") or "").strip()
    description = build_description(story, publish)
    tags = [str(tag).strip() for tag in (publish.get("tags") or []) if str(tag).strip()]
    category = str(publish.get("category") or "SCIENCE_TECHNOLOGY")
    category_map = {
        "SCIENCE_TECHNOLOGY": "28",
        "EDUCATION": "27",
        "ENTERTAINMENT": "24",
    }
    category_id = str(publish.get("categoryId") or category_map.get(category, "28"))
    privacy = str(publish.get("privacyStatus") or "public").lower()
    if privacy not in {"public", "unlisted", "private"}:
        raise SystemExit(f"invalid privacyStatus: {privacy}")

    credentials = Credentials(
        token=None,
        refresh_token=required("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=required("YOUTUBE_CLIENT_ID"),
        client_secret=required("YOUTUBE_CLIENT_SECRET"),
        scopes=[SCOPE],
    )
    credentials.refresh(Request())
    youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:50],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": bool(publish.get("madeForKids", False)),
        },
    }

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
    )
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"YouTube upload progress: {int(status.progress() * 100)}%")

    video_id = response.get("id")
    url = f"https://youtu.be/{video_id}"
    result_path = os.getenv("YOUTUBE_RESULT_PATH", "").strip()
    if result_path:
        Path(result_path).parent.mkdir(parents=True, exist_ok=True)
        Path(result_path).write_text(
            json.dumps(
                {
                    "videoId": video_id,
                    "url": url,
                    "title": title[:100],
                    "description": description,
                    "tags": tags[:50],
                    "hashtags": normalized_hashtags(publish.get("hashtags")),
                    "privacyStatus": privacy,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    print(f"YouTube upload complete: {url}")


if __name__ == "__main__":
    main()
