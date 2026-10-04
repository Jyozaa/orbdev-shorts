from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

USER_AGENT = "orbdev-discovery/1.0 (+https://github.com/Jyozaa/orbdev-shorts)"
STOPWORDS = {
    "the","a","an","and","or","to","of","for","in","on","with","is","are","was","were",
    "this","that","from","new","now","just","ai","artificial","intelligence","video","news",
    "release","released","launch","launched","update","official","about","everything","you","need",
    "here","next","first","also","week","today","latest","more","into","gets","got","has","have"
}
TRANSITION_RE = re.compile(
    r"^(?:all right[, ]+)?(?:first up|next up|also this week|moving on|another (?:one|thing|release)|"
    r"now[, ]+(?:this|we|google|openai|anthropic|microsoft|meta|nvidia)|speaking of)\b",
    re.I,
)
CHAPTER_RE = re.compile(r"(?m)^\s*((?:\d{1,2}:)?\d{1,2}:\d{2})\s+(.+?)\s*$")
URL_RE = re.compile(r"https?://[^\s<>()\[\]{}]+")
SKIP_CHAPTER_WORDS = {"intro","sponsor","sponsored","final thoughts","outro","newsletter","giveaway","ad break"}
TECHNICAL_CUES = {
    "api","sdk","model","models","benchmark","benchmarks","repo","repository","open-source","opensource",
    "open-weight","weights","framework","runtime","compiler","database","gpu","chip","chips","inference",
    "agent","agents","coding","developer","developers","architecture","research","paper","robot","robotics",
    "multimodal","video","image","voice","tts","context","security","vulnerability","exploit","browser",
    "tool","tools","library","protocol","mcp","training","reasoning","token","tokens","operating","cloud",
    "qwen","claude","gemini","deepseek","llama","mistral","flux","ideogram","world-model","world"
}
WEAK_CLUSTER_TOKENS = STOPWORDS | {
    "openai","anthropic","google","microsoft","meta","nvidia","github","huggingface","model","models",
    "agent","agents","developer","developers","tool","tools","research","release","open-source","opensource",
    "system","cloud","video","image","voice","world","benchmark","benchmarks"
}
HARD_EXCLUDE_RE = re.compile(
    r"\b(?:quits?|resigns?|hiring|recruit(?:ing|ment)?|fellowships?|funding round|"
    r"partnership|partners with|election|celebrity|lawsuit|culture is|wiping out humanity|"
    r"executive order|religious scholars|stock(?:s)?|shares|jpmorgan|investors?|market cap|"
    r"medicare fraud|medicaid providers?)\b",
    re.I,
)


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        if value.endswith("Z"):
            return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)
        return datetime.fromisoformat(value).astimezone(timezone.utc)
    except ValueError:
        try:
            return parsedate_to_datetime(value).astimezone(timezone.utc)
        except Exception:
            return None


def age_hours(value: str | None, now: datetime) -> float:
    dt = parse_dt(value)
    if not dt:
        return 9999.0
    return max(0.0, (now - dt).total_seconds() / 3600.0)


def fetch_text(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> tuple[str, str]:
    merged = {"User-Agent": USER_AGENT, "Accept-Language": "en-GB,en;q=0.9"}
    if headers:
        merged.update(headers)
    req = urllib.request.Request(url, headers=merged)
    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace"), response.geturl()


def fetch_json(url: str, headers: dict[str, str] | None = None) -> Any:
    text, _ = fetch_text(url, headers=headers)
    return json.loads(text)


def clean_text(value: str) -> str:
    value = html.unescape(re.sub(r"<[^>]+>", " ", value or ""))
    return re.sub(r"\s+", " ", value).strip()


def tokens(value: str) -> set[str]:
    normalized = re.sub(r"[^a-z0-9.+#-]+", " ", value.lower())
    return {x for x in normalized.split() if len(x) > 2 and x not in STOPWORDS}


def candidate_id(lane: str, title: str, url: str) -> str:
    raw = f"{lane}|{title.lower().strip()}|{url}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def make_candidate(
    lane: str,
    source_kind: str,
    title: str,
    url: str,
    published_at: str | None,
    source_name: str,
    summary: str = "",
    metrics: dict[str, Any] | None = None,
    creator: dict[str, Any] | None = None,
    primary_urls: list[str] | None = None,
    primary_verified: bool = False,
    signals: list[str] | None = None,
) -> dict[str, Any]:
    title = clean_text(title)[:240]
    return {
        "id": candidate_id(lane, title, url),
        "lane": lane,
        "sourceKind": source_kind,
        "title": title,
        "summary": clean_text(summary)[:4000],
        "url": url,
        "publishedAt": published_at,
        "sourceName": source_name,
        "metrics": metrics or {},
        "creator": creator,
        "primaryUrls": primary_urls or [],
        "primaryVerified": primary_verified,
        "signals": signals or [],
    }


def freshness_points(candidate: dict[str, Any], now: datetime, window: float = 48.0) -> float:
    age = age_hours(candidate.get("publishedAt"), now)
    return max(0.0, 2.0 * (1.0 - min(age, window) / window))


def domain(url: str) -> str:
    return urllib.parse.urlparse(url).netloc.lower().removeprefix("www.")


def is_primary_domain(url: str, primary_domains: list[str]) -> bool:
    host = domain(url)
    return any(host == d or host.endswith("." + d) for d in primary_domains)


def google_news_candidates(config: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lookback = int(config["candidateLookbackHours"])
    for query in config["majorNews"]["queries"]:
        q = f"({query}) when:2d"
        url = (
            "https://news.google.com/rss/search?q="
            + urllib.parse.quote_plus(q)
            + "&hl=en-GB&gl=GB&ceid=GB:en"
        )
        try:
            xml_text, _ = fetch_text(url)
            root = ET.fromstring(xml_text)
        except Exception as exc:
            print(f"major-news query failed: {query}: {exc}", file=sys.stderr)
            continue
        for item in root.findall(".//item")[:35]:
            title = clean_text(item.findtext("title") or "")
            link = clean_text(item.findtext("link") or "")
            pub = item.findtext("pubDate")
            if not title or not link or age_hours(pub, now) > lookback:
                continue
            source_el = item.find("source")
            source_name = clean_text(source_el.text if source_el is not None and source_el.text else "Google News")
            out.append(
                make_candidate(
                    "major_news",
                    "news_search",
                    title,
                    link,
                    iso(parse_dt(pub) or now),
                    source_name,
                    signals=["major-news-search"],
                )
            )
    return out


def github_candidates(config: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    days = int(config["hotEmerging"]["githubCreatedWithinDays"])
    since = (now - timedelta(days=days)).date().isoformat()
    min_stars = int(config["hotEmerging"]["githubMinStars"])
    out: list[dict[str, Any]] = []
    for base_query in config["hotEmerging"]["githubQueries"]:
        q = f"{base_query} created:>={since} stars:>={min_stars}"
        url = "https://api.github.com/search/repositories?" + urllib.parse.urlencode(
            {"q": q, "sort": "stars", "order": "desc", "per_page": 30}
        )
        try:
            payload = fetch_json(url, headers=headers)
        except Exception as exc:
            print(f"github query failed: {base_query}: {exc}", file=sys.stderr)
            continue
        for repo in payload.get("items", []):
            created = repo.get("created_at")
            age = max(age_hours(created, now), 1.0)
            stars = int(repo.get("stargazers_count") or 0)
            forks = int(repo.get("forks_count") or 0)
            out.append(
                make_candidate(
                    "hot_emerging",
                    "github_repo",
                    repo.get("full_name") or repo.get("name") or "GitHub project",
                    repo.get("html_url") or "",
                    created,
                    "GitHub",
                    repo.get("description") or "",
                    {
                        "stars": stars,
                        "forks": forks,
                        "ageHours": round(age, 2),
                        "starsPerHour": round(stars / age, 2),
                    },
                    primary_urls=[repo.get("html_url") or ""],
                    primary_verified=True,
                    signals=["github", "open-source", "momentum"],
                )
            )
    return out


def hacker_news_candidates(config: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    min_points = int(config["hotEmerging"]["hackerNewsMinPoints"])
    min_created = int((now - timedelta(hours=int(config["candidateLookbackHours"]))).timestamp())
    for query in config["hotEmerging"]["hackerNewsQueries"]:
        params = {
            "query": query,
            "tags": "story",
            "numericFilters": f"created_at_i>{min_created},points>{min_points}",
            "hitsPerPage": 40,
        }
        url = "https://hn.algolia.com/api/v1/search_by_date?" + urllib.parse.urlencode(params)
        try:
            payload = fetch_json(url)
        except Exception as exc:
            print(f"hacker-news query failed: {query}: {exc}", file=sys.stderr)
            continue
        for hit in payload.get("hits", []):
            target = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
            out.append(
                make_candidate(
                    "hot_emerging",
                    "hacker_news",
                    hit.get("title") or "Hacker News story",
                    target,
                    hit.get("created_at"),
                    "Hacker News",
                    metrics={
                        "points": int(hit.get("points") or 0),
                        "comments": int(hit.get("num_comments") or 0),
                    },
                    primary_urls=[target] if domain(target) in {"github.com", "huggingface.co", "arxiv.org"} else [],
                    primary_verified=domain(target) in {"github.com", "huggingface.co", "arxiv.org"},
                    signals=["hacker-news", "developer-discussion"],
                )
            )
    return out


def huggingface_candidates(config: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    limit = int(config["hotEmerging"]["huggingFaceLimit"])
    url = "https://huggingface.co/api/models?" + urllib.parse.urlencode(
        {"sort": "trendingScore", "direction": "-1", "limit": limit, "full": "true"}
    )
    try:
        payload = fetch_json(url)
    except Exception as exc:
        print(f"hugging-face scan failed: {exc}", file=sys.stderr)
        return []
    out: list[dict[str, Any]] = []
    for model in payload if isinstance(payload, list) else []:
        model_id = model.get("id") or model.get("modelId")
        if not model_id:
            continue
        published = model.get("createdAt") or model.get("lastModified")
        if age_hours(published, now) > int(config["exceptionLookbackHours"]):
            continue
        model_url = f"https://huggingface.co/{model_id}"
        tags = model.get("tags") or []
        out.append(
            make_candidate(
                "hot_emerging",
                "huggingface_model",
                model_id,
                model_url,
                published,
                "Hugging Face",
                " ".join(str(t) for t in tags[:20]),
                {
                    "likes": int(model.get("likes") or 0),
                    "downloads": int(model.get("downloads") or 0),
                    "trendingScore": float(model.get("trendingScore") or 0),
                },
                primary_urls=[model_url],
                primary_verified=True,
                signals=["hugging-face", "open-model", "momentum"],
            )
        )
    return out


def resolve_youtube_channel_id(channel_url: str) -> str | None:
    try:
        text, _ = fetch_text(channel_url)
    except Exception:
        return None
    patterns = [
        r'"channelId":"(UC[A-Za-z0-9_-]{20,})"',
        r'<meta\s+itemprop="channelId"\s+content="(UC[A-Za-z0-9_-]{20,})"',
        r'"externalId":"(UC[A-Za-z0-9_-]{20,})"',
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def youtube_feed(channel_id: str) -> list[dict[str, Any]]:
    url = "https://www.youtube.com/feeds/videos.xml?" + urllib.parse.urlencode({"channel_id": channel_id})
    text, _ = fetch_text(url)
    root = ET.fromstring(text)
    ns = {
        "a": "http://www.w3.org/2005/Atom",
        "yt": "http://www.youtube.com/xml/schemas/2015",
        "media": "http://search.yahoo.com/mrss/",
    }
    videos = []
    for entry in root.findall("a:entry", ns):
        video_id = entry.findtext("yt:videoId", default="", namespaces=ns)
        title = entry.findtext("a:title", default="", namespaces=ns)
        published = entry.findtext("a:published", default="", namespaces=ns)
        link_el = entry.find("a:link", ns)
        video_url = link_el.attrib.get("href", "") if link_el is not None else ""
        desc = entry.findtext("media:group/media:description", default="", namespaces=ns)
        videos.append(
            {
                "videoId": video_id,
                "title": title,
                "publishedAt": published,
                "url": video_url or f"https://www.youtube.com/watch?v={video_id}",
                "description": desc,
            }
        )
    return videos


def fetch_transcript(video_id: str) -> list[dict[str, Any]]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except Exception:
        return []
    try:
        api = YouTubeTranscriptApi()
        fetched = api.fetch(video_id, languages=["en", "en-US", "en-GB"])
        snippets = getattr(fetched, "snippets", fetched)
        out = []
        for item in snippets:
            if isinstance(item, dict):
                text = item.get("text", "")
                start = float(item.get("start", 0))
                duration = float(item.get("duration", 0))
            else:
                text = getattr(item, "text", "")
                start = float(getattr(item, "start", 0))
                duration = float(getattr(item, "duration", 0))
            if text:
                out.append({"text": clean_text(text), "start": start, "duration": duration})
        return out
    except Exception as exc:
        print(f"transcript unavailable for {video_id}: {type(exc).__name__}", file=sys.stderr)
        return []


def chapter_seconds(value: str) -> int:
    parts = [int(x) for x in value.split(":")]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def chapters_from_description(description: str) -> list[dict[str, Any]]:
    chapters = []
    for stamp, title in CHAPTER_RE.findall(description or ""):
        lower = title.lower()
        if any(word in lower for word in SKIP_CHAPTER_WORDS):
            continue
        chapters.append({"start": chapter_seconds(stamp), "title": clean_text(title)})
    return chapters


def transcript_excerpt(transcript: list[dict[str, Any]], start: float, end: float | None) -> str:
    parts = []
    for item in transcript:
        t = float(item.get("start", 0))
        if t < start:
            continue
        if end is not None and t >= end:
            break
        parts.append(item.get("text", ""))
        if sum(len(p) for p in parts) > 2400:
            break
    return clean_text(" ".join(parts))


def transition_segments(transcript: list[dict[str, Any]], max_segments: int) -> list[dict[str, Any]]:
    if not transcript:
        return []
    starts = [0]
    last_start = 0.0
    for i, item in enumerate(transcript):
        t = float(item.get("start", 0))
        text = item.get("text", "")
        if t - last_start >= 40 and TRANSITION_RE.search(text):
            starts.append(i)
            last_start = t
            if len(starts) >= max_segments:
                break
    if len(starts) < 2:
        return []
    starts.append(len(transcript))
    segments = []
    for left, right in zip(starts, starts[1:]):
        items = transcript[left:right]
        if not items:
            continue
        body = clean_text(" ".join(x.get("text", "") for x in items))
        if len(body.split()) < 45:
            continue
        first = body.split(".")[0].strip()
        first = re.sub(
            r"^(?:all right[, ]+)?(?:first up|next up|also this week|moving on|another (?:one|thing|release)|speaking of)[,: ]*",
            "",
            first,
            flags=re.I,
        )
        label = " ".join(first.split()[:16]) or "Creator topic"
        segments.append(
            {
                "start": float(items[0].get("start", 0)),
                "title": label,
                "text": body[:4000],
            }
        )
    return segments[:max_segments]


def creator_candidates(config: dict[str, Any], now: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    radar = config["creatorRadar"]
    lookback = int(radar["videoLookbackHours"])
    max_videos = int(radar["maxVideosPerCreator"])
    max_segments = int(radar["maxSegmentsPerVideo"])
    primary_domains = config["majorNews"]["primaryDomains"]
    out: list[dict[str, Any]] = []
    seen_videos: list[str] = []
    for creator in radar["creators"]:
        channel_id = resolve_youtube_channel_id(creator["url"])
        if not channel_id:
            print(f"creator channel id unavailable: {creator['name']}", file=sys.stderr)
            continue
        try:
            videos = youtube_feed(channel_id)
        except Exception as exc:
            print(f"creator feed failed: {creator['name']}: {exc}", file=sys.stderr)
            continue
        recent = [v for v in videos if age_hours(v.get("publishedAt"), now) <= lookback][:max_videos]
        for video in recent:
            seen_videos.append(video["videoId"])
            transcript = fetch_transcript(video["videoId"])
            description = video.get("description") or ""
            all_links = [u.rstrip(".,)") for u in URL_RE.findall(description)]
            primary_links = [u for u in all_links if is_primary_domain(u, primary_domains)]
            chapters = chapters_from_description(description)
            segments: list[dict[str, Any]] = []
            if len(chapters) >= 2:
                for i, chapter in enumerate(chapters[:max_segments]):
                    next_start = chapters[i + 1]["start"] if i + 1 < len(chapters) else None
                    segments.append(
                        {
                            "start": chapter["start"],
                            "title": chapter["title"],
                            "text": transcript_excerpt(transcript, chapter["start"], next_start),
                        }
                    )
            if not segments:
                segments = transition_segments(transcript, max_segments)
            if not segments:
                segments = [{"start": 0, "title": video["title"], "text": transcript_excerpt(transcript, 0, None)}]

            for index, segment in enumerate(segments):
                title = segment["title"]
                if title.lower() in SKIP_CHAPTER_WORDS:
                    continue
                segment_url = video["url"] + (f"&t={int(segment['start'])}s" if segment["start"] else "")
                out.append(
                    make_candidate(
                        "creator_radar",
                        "creator_video_topic",
                        title,
                        segment_url,
                        video["publishedAt"],
                        creator["name"],
                        segment["text"] or video["title"],
                        {
                            "videoId": video["videoId"],
                            "segmentIndex": index,
                            "segmentStartSeconds": segment["start"],
                            "discoveryWeight": creator["discoveryWeight"],
                        },
                        creator={
                            "name": creator["name"],
                            "handle": creator["handle"],
                            "category": creator["category"],
                            "videoTitle": video["title"],
                            "videoUrl": video["url"],
                        },
                        primary_urls=primary_links,
                        primary_verified=False,
                        signals=["creator-radar", creator["category"], "creator-mention"],
                    )
                )
    return out, seen_videos


def technical_core(candidate: dict[str, Any]) -> bool:
    kind = candidate.get("sourceKind")
    if kind in {"github_repo", "huggingface_model"}:
        return True
    text = f"{candidate.get('title','')} {candidate.get('summary','')}"
    if HARD_EXCLUDE_RE.search(text):
        return False
    if candidate.get("sourceKind") in {"news_search", "hacker_news"} and str(candidate.get("title", "")).count(";") >= 2:
        return False
    ts = tokens(text)
    if ts & TECHNICAL_CUES:
        return True
    # Distinct model/version tokens are technical even if a generic cue is absent.
    if any(any(ch.isdigit() for ch in token) and len(token) >= 4 for token in ts):
        return True
    return False


def raw_score(candidate: dict[str, Any], now: datetime) -> float:
    kind = candidate["sourceKind"]
    fresh = freshness_points(candidate, now)
    metrics = candidate.get("metrics") or {}
    if kind == "news_search":
        return min(10.0, 5.4 + fresh)
    if kind == "github_repo":
        stars = float(metrics.get("stars", 0))
        velocity = float(metrics.get("starsPerHour", 0))
        momentum = min(2.5, math.log10(stars + 1) * 0.75)
        velocity_score = min(1.8, math.log10(velocity + 1) * 0.9)
        return min(10.0, 3.2 + fresh * 0.55 + momentum + velocity_score)
    if kind == "hacker_news":
        points = float(metrics.get("points", 0))
        comments = float(metrics.get("comments", 0))
        return min(10.0, 3.6 + fresh * 0.6 + min(points / 80, 2.2) + min(comments / 80, 1.2))
    if kind == "huggingface_model":
        likes = float(metrics.get("likes", 0))
        downloads = float(metrics.get("downloads", 0))
        trending = float(metrics.get("trendingScore", 0))
        return min(
            10.0,
            3.7
            + fresh * 0.6
            + min(math.log10(likes + 1) * 0.65, 1.5)
            + min(math.log10(downloads + 1) * 0.35, 1.5)
            + min(trending / 20, 1.0),
        )
    if kind == "creator_video_topic":
        weight = float(metrics.get("discoveryWeight", 1.0))
        return min(10.0, 4.9 + fresh * 0.8 + (weight - 1.0) * 2.0)
    return min(10.0, 4.0 + fresh)


def similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    title_a = tokens(a.get("title", ""))
    title_b = tokens(b.get("title", ""))
    ta = title_a | tokens(a.get("summary", "")[:260])
    tb = title_b | tokens(b.get("summary", "")[:260])
    if not ta or not tb:
        return 0.0
    common = ta & tb
    base = (len(common) / min(len(ta), len(tb))) if common else 0.0
    title_common = title_a & title_b
    strong = {
        token for token in title_common
        if token not in WEAK_CLUSTER_TOKENS
        and (len(token) >= 6 or any(ch.isdigit() for ch in token))
    }
    # Only title-level distinctive entities can bypass normal similarity. This
    # joins differently-worded coverage of the same named model/repo without
    # collapsing unrelated articles that merely share summary vocabulary.
    if strong:
        return max(base, 0.58)
    if len(common) < 2:
        return 0.0
    return base


def cluster_candidates(candidates: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    ordered = sorted(candidates, key=lambda x: float(x.get("rawScore", 0)), reverse=True)
    clusters: list[list[dict[str, Any]]] = []
    for candidate in ordered:
        best_index = -1
        best_score = 0.0
        for i, cluster in enumerate(clusters):
            score = max(similarity(candidate, other) for other in cluster[:6])
            if score > best_score:
                best_score = score
                best_index = i
        if best_index >= 0 and best_score >= 0.52:
            clusters[best_index].append(candidate)
        else:
            clusters.append([candidate])
    return clusters


def covered_tokens(covered: dict[str, Any], current_story: dict[str, Any] | None) -> list[set[str]]:
    values = []
    for story in covered.get("stories", []):
        values.append(tokens(str(story.get("headline", "")) + " " + str(story.get("storyKey", ""))))
    if current_story:
        values.append(tokens(str(current_story.get("title", "")) + " " + str(current_story.get("editorial", {}).get("storyKey", ""))))
    return [v for v in values if v]


def already_covered(cluster: list[dict[str, Any]], fingerprints: list[set[str]]) -> bool:
    cluster_terms = set().union(*(tokens(c.get("title", "") + " " + c.get("summary", "")[:220]) for c in cluster))
    if len(cluster_terms) < 2:
        return False
    for fp in fingerprints:
        common = cluster_terms & fp
        if len(common) >= 2 and len(common) / min(len(cluster_terms), len(fp)) >= 0.55:
            return True
    return False


def summarize_cluster(
    cluster: list[dict[str, Any]],
    config: dict[str, Any],
    covered_fps: list[set[str]],
) -> dict[str, Any]:
    best = max(cluster, key=lambda x: float(x.get("rawScore", 0)))
    lanes = sorted({c["lane"] for c in cluster})
    creator_categories = sorted(
        {
            c.get("creator", {}).get("category")
            for c in cluster
            if isinstance(c.get("creator"), dict) and c.get("creator", {}).get("category")
        }
    )
    creators = sorted(
        {
            c.get("creator", {}).get("name")
            for c in cluster
            if isinstance(c.get("creator"), dict) and c.get("creator", {}).get("name")
        }
    )
    sources = sorted({c.get("sourceName", "") for c in cluster if c.get("sourceName")})
    heat = config["heatSignals"]
    score = float(best["rawScore"])
    score += max(0, len(lanes) - 1) * float(heat["additionalLane"])
    score += max(0, len(sources) - 1) * float(heat["additionalIndependentSource"])
    score += max(0, len(creator_categories) - 1) * float(heat["additionalCreatorCategory"])
    if any(c["sourceKind"] == "github_repo" for c in cluster):
        score += float(heat["githubTrending"])
    if any(c["sourceKind"] == "hacker_news" for c in cluster):
        score += float(heat["hackerNews"])
    if any(c["sourceKind"] == "huggingface_model" for c in cluster):
        score += float(heat["huggingFaceTrending"])
    if creators:
        score += float(heat["creatorMention"])
    score = round(min(10.0, score), 2)
    covered = already_covered(cluster, covered_fps)
    primary_urls = sorted({u for c in cluster for u in c.get("primaryUrls", []) if u})
    primary_verified = any(bool(c.get("primaryVerified")) for c in cluster)
    qualifies = score >= float(config["qualificationScore"]) and not covered
    return {
        "clusterId": hashlib.sha1("|".join(sorted(c["id"] for c in cluster)).encode()).hexdigest()[:16],
        "title": best["title"],
        "score": score,
        "qualifiesForEditorial": qualifies,
        "publishReady": False,
        "primarySourceAvailable": bool(primary_urls) or primary_verified,
        "needsPrimaryVerification": qualifies and not primary_verified,
        "needsEditorialVerification": qualifies,
        "alreadyCovered": covered,
        "lanes": lanes,
        "creatorCategories": creator_categories,
        "creators": creators,
        "sourceNames": sources,
        "primaryUrls": primary_urls,
        "signals": sorted({s for c in cluster for s in c.get("signals", [])}),
        "bestCandidate": best,
        "evidence": sorted(cluster, key=lambda x: float(x.get("rawScore", 0)), reverse=True),
    }


def load_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    return json.loads(path.read_text(encoding="utf-8"))


def write_report(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Orbdev discovery scan",
        "",
        f"Generated: {result['generatedAt']}",
        f"Candidates: {result['candidateCount']}",
        f"Clusters: {result['clusterCount']}",
        f"Qualified for editorial: {len(result['qualified'])}",
        "",
        "## Lane summary",
        "",
    ]
    for lane, counts in result["laneSummary"].items():
        lines.append(f"- {lane}: {counts['raw']} raw / {counts['qualified']} qualifying clusters")
    lines += ["", "## Qualifying topics", ""]
    if not result["qualified"]:
        lines.append("No topic cleared the quality threshold in this scan.")
    for item in result["qualified"]:
        suffix = "primary source found" if item.get("primarySourceAvailable") else "needs primary verification"
        lines.append(
            f"- {item['score']:.2f} — {item['title']} "
            f"[{', '.join(item['lanes'])}; {suffix}]"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="editorial/discovery.json")
    parser.add_argument("--policy", default="editorial/policy.json")
    parser.add_argument("--covered", default="history/covered.json")
    parser.add_argument("--state", default="history/discovery-state.json")
    parser.add_argument("--current", default="stories/current.json")
    parser.add_argument("--output", default="build/discovery")
    args = parser.parse_args()

    now = now_utc()
    config = load_json(Path(args.config), {})
    policy = load_json(Path(args.policy), {})
    covered = load_json(Path(args.covered), {"stories": []})
    current_story = load_json(Path(args.current), None)
    old_state = load_json(Path(args.state), {"version": 1})

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    candidates: list[dict[str, Any]] = []
    candidates.extend(google_news_candidates(config, now))
    candidates.extend(github_candidates(config, now))
    candidates.extend(hacker_news_candidates(config, now))
    candidates.extend(huggingface_candidates(config, now))
    creator_items, seen_videos = creator_candidates(config, now)
    candidates.extend(creator_items)

    technical_rejected = [candidate for candidate in candidates if not technical_core(candidate)]
    candidates = [candidate for candidate in candidates if technical_core(candidate)]
    if technical_rejected:
        print(f"Technical-core filter rejected {len(technical_rejected)} non-technical candidates")

    unique: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        candidate["rawScore"] = round(raw_score(candidate, now), 2)
        old = unique.get(candidate["id"])
        if old is None or candidate["rawScore"] > old["rawScore"]:
            unique[candidate["id"]] = candidate
    candidates = list(unique.values())

    clusters = cluster_candidates(candidates)
    covered_fps = covered_tokens(covered, current_story)
    cluster_rows = [summarize_cluster(cluster, config, covered_fps) for cluster in clusters]
    cluster_rows.sort(key=lambda x: x["score"], reverse=True)
    qualified = [row for row in cluster_rows if row["qualifiesForEditorial"]]

    lane_summary = {}
    for lane in ("major_news", "hot_emerging", "creator_radar"):
        lane_summary[lane] = {
            "raw": sum(1 for c in candidates if c["lane"] == lane),
            "qualified": sum(1 for row in qualified if lane in row["lanes"]),
        }

    result = {
        "version": 1,
        "generatedAt": iso(now),
        "scanCadenceHours": config["scanCadenceHours"],
        "qualificationScore": config["qualificationScore"],
        "candidateCount": len(candidates),
        "clusterCount": len(cluster_rows),
        "laneSummary": lane_summary,
        "qualified": qualified,
        "allClusters": cluster_rows,
    }
    (output / "candidates.json").write_text(json.dumps(candidates, indent=2), encoding="utf-8")
    (output / "clusters.json").write_text(json.dumps(cluster_rows, indent=2), encoding="utf-8")
    (output / "qualified.json").write_text(
        json.dumps(
            {
                "version": 1,
                "generatedAt": result["generatedAt"],
                "scanCadenceHours": config["scanCadenceHours"],
                "qualified": qualified,
                "laneSummary": {k: v["qualified"] for k, v in lane_summary.items()},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    write_report(output / "scan-report.md", result)

    recent_ids = [c["id"] for c in sorted(candidates, key=lambda x: x["rawScore"], reverse=True)[:500]]
    next_state = {
        "version": 1,
        "lastScanAt": result["generatedAt"],
        "seenCreatorVideos": sorted(set((old_state.get("seenCreatorVideos") or []) + seen_videos))[-500:],
        "recentCandidateIds": recent_ids,
    }
    (output / "next-state.json").write_text(json.dumps(next_state, indent=2), encoding="utf-8")

    print(
        f"Discovery scan: {len(candidates)} candidates -> {len(cluster_rows)} clusters -> "
        f"{len(qualified)} editorial-qualified"
    )
    for lane, counts in lane_summary.items():
        print(f"  {lane}: {counts['raw']} raw / {counts['qualified']} qualifying")
    for item in qualified[:20]:
        status = "primary-found" if item.get("primarySourceAvailable") else "verify-primary"
        print(f"  {item['score']:.2f} {status}: {item['title']}")


if __name__ == "__main__":
    main()
