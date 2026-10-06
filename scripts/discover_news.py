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
    "qwen","claude","gemini","deepseek","llama","mistral","flux","ideogram","world-model","world",
    "mathematics","mathematical","theorem","proof","conjecture","prime","primes","geometry","topology",
    "algebra","combinatorics","cryptography","algorithm","algorithms","quantum","physics","scientific",
    "breach","breaches","leak","leaks","hack","hacked","hacker","hackers","ransomware",
    "cyberattack","cyberattacks","malware","botnet","phishing","ddos","extortion",
    "zero-day","zeroday","cve","intrusion","compromise","compromised","credentials","credential",
    "supply-chain","backdoor","exfiltration","incident","cybersecurity"
}
MARKET_CUES = {
    "earnings","revenue","revenues","guidance","profit","profits","margin","margins","valuation",
    "acquisition","acquires","acquired","merger","mergers","buyout","ipo","shares","stock","stocks",
    "market","market-cap","capex","investment","investments","invests","financing","funding",
    "contract","contracts","deal","deals","restructuring","layoffs","layoff","job-cuts","spending",
    "forecast","forecasts","sales","bookings","backlog","dividend","buyback"
}
MARKET_ENTITY_NAMES = (
    "openai","anthropic","google","alphabet","microsoft","meta","nvidia","amazon","aws","apple",
    "oracle","ibm","amd","intel","broadcom","salesforce","adobe","servicenow","palantir",
    "accenture","deloitte","pwc","pricewaterhousecoopers","ey","ernst & young","kpmg",
    "mckinsey","boston consulting group","bcg","bain","capgemini","cognizant","infosys",
    "tata consultancy services","tcs"
)
WEAK_CLUSTER_TOKENS = STOPWORDS | {
    "openai","anthropic","google","microsoft","meta","nvidia","github","huggingface","model","models",
    "agent","agents","developer","developers","tool","tools","research","release","open-source","opensource",
    "system","cloud","video","image","voice","world","benchmark","benchmarks"
}
LOW_SIGNAL_NEWS_SOURCES = {
    "tradingview", "stocktwits", "aol.co.uk", "finance.biggo.com"
}
HARD_EXCLUDE_RE = re.compile(
    r"\b(?:quits?|resigns?|hiring|recruit(?:ing|ment)?|fellowships?|election|celebrity|"
    r"culture is|wiping out humanity|executive order|religious scholars|"
    r"medicare fraud|medicaid providers?|consumer tech roundup)\b",
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
    related_urls: list[str] | None = None,
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
        "relatedUrls": related_urls or [],
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


def google_news_candidates(
    config: dict[str, Any],
    now: datetime,
    section: str = "majorNews",
    lane: str = "major_news",
    signal: str = "major-news-search",
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    lookback = int(config["candidateLookbackHours"])
    section_config = config.get(section) or {}
    primary_domains = section_config.get("primaryDomains") or config["majorNews"]["primaryDomains"]
    publisher_bonuses = {
        str(k).lower(): float(v)
        for k, v in (section_config.get("publisherBonuses") or config["majorNews"].get("publisherBonuses") or {}).items()
    }
    news_lookback_days = max(2, math.ceil(lookback / 24))
    for query in section_config.get("queries", []):
        q = f"({query}) when:{news_lookback_days}d"
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
            source_home = clean_text(source_el.attrib.get("url", "")) if source_el is not None else ""
            source_is_primary = bool(source_home and is_primary_domain(source_home, primary_domains))
            source_bonus = publisher_bonuses.get(source_name.lower(), 0.0)
            signals = [signal]
            if source_is_primary:
                signals.append("primary-publisher")
            out.append(
                make_candidate(
                    lane,
                    "news_search",
                    title,
                    link,
                    iso(parse_dt(pub) or now),
                    source_name,
                    metrics={
                        "publisherBonus": source_bonus,
                        "publisherUrl": source_home,
                        "primaryPublisher": source_is_primary,
                    },
                    signals=signals,
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


def github_trending_candidates(config: dict[str, Any], now: datetime) -> list[dict[str, Any]]:
    hot = config["hotEmerging"]
    windows = hot.get("githubTrendingWindows", ["daily", "weekly"])
    per_window = int(hot.get("githubTrendingLimit", 18))
    token = os.getenv("GITHUB_TOKEN", "")
    api_headers = {"Accept": "application/vnd.github+json"}
    if token:
        api_headers["Authorization"] = f"Bearer {token}"

    discovered: dict[str, dict[str, Any]] = {}
    for window in windows:
        url = "https://github.com/trending?" + urllib.parse.urlencode({"since": window})
        try:
            page, _ = fetch_text(url)
        except Exception as exc:
            print(f"github trending failed ({window}): {exc}", file=sys.stderr)
            continue

        articles = re.findall(r'<article[^>]*class="[^"]*Box-row[^"]*"[^>]*>(.*?)</article>', page, re.S | re.I)
        for article in articles[:per_window]:
            repo_match = re.search(
                r'<h2[^>]*>.*?href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"',
                article,
                re.S | re.I,
            )
            if not repo_match:
                continue
            slug = repo_match.group(1)
            owner = slug.split("/", 1)[0].lower()
            if owner in {"sponsors", "topics", "collections", "marketplace"}:
                continue

            clean_article = clean_text(article)
            recent_match = re.search(r'([\d,]+)\s+stars?\s+(today|this week)', clean_article, re.I)
            stars_recent = int(recent_match.group(1).replace(",", "")) if recent_match else 0
            days = 7.0 if window == "weekly" else 1.0
            stars_per_day = stars_recent / days
            key = slug.lower()
            old = discovered.get(key)
            if old and float(old["starsPerDay"]) >= stars_per_day:
                continue
            discovered[key] = {
                "slug": slug,
                "window": window,
                "starsRecent": stars_recent,
                "starsPerDay": round(stars_per_day, 2),
            }

    out: list[dict[str, Any]] = []
    for row in discovered.values():
        slug = row["slug"]
        repo_url = f"https://github.com/{slug}"
        repo: dict[str, Any] = {}
        try:
            repo = fetch_json(f"https://api.github.com/repos/{slug}", headers=api_headers)
        except Exception as exc:
            print(f"github trending repo metadata failed ({slug}): {exc}", file=sys.stderr)

        created = repo.get("created_at")
        pushed = repo.get("pushed_at")
        stars = int(repo.get("stargazers_count") or 0)
        forks = int(repo.get("forks_count") or 0)
        stars_recent = int(row["starsRecent"])
        stars_per_day = float(row["starsPerDay"])
        description = repo.get("description") or ""
        out.append(
            make_candidate(
                "hot_emerging",
                "github_trending",
                repo.get("full_name") or slug,
                repo.get("html_url") or repo_url,
                iso(now),
                "GitHub Trending",
                description,
                {
                    "stars": stars,
                    "forks": forks,
                    "starsRecent": stars_recent,
                    "starsPerDay": stars_per_day,
                    "trendingWindow": row["window"],
                    "repoCreatedAt": created,
                    "repoPushedAt": pushed,
                },
                primary_urls=[repo.get("html_url") or repo_url],
                primary_verified=True,
                signals=["github", "github-trending", "open-source", "momentum"],
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


def youtube_page_time(text: str, now: datetime) -> str | None:
    value = clean_text(text).lower()
    value = re.sub(r"^(streamed|premiered)\s+", "", value)
    if value in {"today", "just now"}:
        return iso(now)
    match = re.search(r"(\d+)\s+(minute|hour|day|week|month|year)s?\s+ago", value)
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    seconds = {
        "minute": 60,
        "hour": 3600,
        "day": 86400,
        "week": 7 * 86400,
        "month": 30 * 86400,
        "year": 365 * 86400,
    }[unit] * amount
    return iso(now - timedelta(seconds=seconds))


def youtube_channel_page_videos(
    channel_url: str,
    now: datetime,
    max_videos: int,
) -> list[dict[str, Any]]:
    target = channel_url.rstrip("/")
    if not target.endswith("/videos"):
        target += "/videos"
    try:
        html, _ = fetch_text(target, timeout=20)
    except Exception as exc:
        print(
            f"creator channel page failed: {channel_url}: {type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return []

    payload = None
    decoder = json.JSONDecoder()
    for pattern in (
        r"var\s+ytInitialData\s*=\s*",
        r'window\["ytInitialData"\]\s*=\s*',
        r"ytInitialData\s*=\s*",
    ):
        for match in re.finditer(pattern, html):
            start = html.find("{", match.end())
            if start < 0:
                continue
            try:
                payload, _ = decoder.raw_decode(html[start:])
                break
            except Exception:
                continue
        if payload is not None:
            break
    if payload is None:
        print(f"creator channel page missing ytInitialData: {channel_url}", file=sys.stderr)
        return []

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def text_value(value: object) -> str:
        if not isinstance(value, dict):
            return ""
        simple = value.get("simpleText")
        if isinstance(simple, str):
            return clean_text(simple)
        runs = value.get("runs")
        if isinstance(runs, list):
            return clean_text("".join(
                str(row.get("text") or "")
                for row in runs
                if isinstance(row, dict)
            ))
        return ""

    def visit(node: object) -> None:
        if isinstance(node, dict):
            for key in ("videoRenderer", "gridVideoRenderer"):
                renderer = node.get(key)
                if not isinstance(renderer, dict):
                    continue
                video_id = str(renderer.get("videoId") or "").strip()
                if not video_id or video_id in seen:
                    continue
                title = text_value(renderer.get("title")) or "Creator video"
                published_text = text_value(renderer.get("publishedTimeText"))
                published_at = youtube_page_time(published_text, now)
                if not published_at:
                    continue
                description = text_value(renderer.get("descriptionSnippet"))
                seen.add(video_id)
                rows.append({
                    "videoId": video_id,
                    "title": title,
                    "publishedAt": published_at,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "description": description,
                })
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(payload)
    return rows[:max_videos]


def youtube_channel_videos(channel_url: str, max_videos: int) -> list[dict[str, Any]]:
    """List recent channel videos without relying on YouTube's RSS endpoint."""
    try:
        import yt_dlp
    except Exception as exc:
        print(f"yt-dlp unavailable: {type(exc).__name__}", file=sys.stderr)
        return []

    target = channel_url.rstrip("/")
    if not target.endswith("/videos"):
        target += "/videos"

    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": "in_playlist",
        "playlistend": max(max_videos * 2, 12),
        "ignoreerrors": True,
    }
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            payload = ydl.extract_info(target, download=False) or {}
    except Exception as exc:
        print(f"creator yt-dlp listing failed: {channel_url}: {type(exc).__name__}: {exc}", file=sys.stderr)
        return []

    videos: list[dict[str, Any]] = []
    detail_options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "ignoreerrors": True,
    }
    for entry in payload.get("entries") or []:
        if not isinstance(entry, dict):
            continue
        video_id = str(entry.get("id") or "").strip()
        if not video_id:
            continue
        watch_url = f"https://www.youtube.com/watch?v={video_id}"

        def published_from(item: dict[str, Any]) -> str | None:
            timestamp = item.get("timestamp") or item.get("release_timestamp")
            if isinstance(timestamp, (int, float)):
                return iso(datetime.fromtimestamp(float(timestamp), tz=timezone.utc))
            upload_date = str(item.get("upload_date") or "").strip()
            if re.fullmatch(r"\d{8}", upload_date):
                return iso(datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc))
            return None

        published_at = published_from(entry)
        detailed = entry
        if not published_at:
            try:
                with yt_dlp.YoutubeDL(detail_options) as ydl:
                    full = ydl.extract_info(watch_url, download=False)
                if isinstance(full, dict):
                    detailed = full
                    published_at = published_from(full)
            except Exception as exc:
                print(
                    f"creator video metadata unavailable: {video_id}: "
                    f"{type(exc).__name__}",
                    file=sys.stderr,
                )

        if not published_at:
            print(f"creator video date unavailable: {video_id}", file=sys.stderr)
            continue

        videos.append(
            {
                "videoId": video_id,
                "title": clean_text(str(detailed.get("title") or entry.get("title") or "Creator video")),
                "publishedAt": published_at,
                "url": watch_url,
                "description": clean_text(str(detailed.get("description") or entry.get("description") or "")),
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


def creator_candidates(
    config: dict[str, Any],
    now: datetime,
    seen_video_ids: set[str] | None = None,
) -> tuple[list[dict[str, Any]], list[str]]:
    radar = config["creatorRadar"]
    lookback = int(radar["videoLookbackHours"])
    max_videos = int(radar["maxVideosPerCreator"])
    default_max_segments = int(radar["maxSegmentsPerVideo"])
    primary_domains = config["majorNews"]["primaryDomains"]
    already_seen = seen_video_ids or set()
    out: list[dict[str, Any]] = []
    processed_videos: list[str] = []

    for creator in radar["creators"]:
        channel_id = str(creator.get("channelId") or "").strip() or resolve_youtube_channel_id(creator["url"])
        if not channel_id:
            print(f"creator channel id unavailable: {creator['name']}", file=sys.stderr)
            continue
        try:
            videos = youtube_feed(channel_id)
        except Exception as exc:
            print(f"creator RSS failed: {creator['name']}: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            videos = []
        if not videos:
            videos = youtube_channel_page_videos(creator["url"],now,max(max_videos*2,12))
        if not videos:
            print(f"creator page empty: {creator['name']}; trying yt-dlp",file=sys.stderr)
            videos = youtube_channel_videos(creator["url"],max_videos)
        if not videos:
            print(f"creator listing unavailable: {creator['name']}", file=sys.stderr)
            continue

        recent = [
            v for v in videos
            if v.get("videoId")
            and v["videoId"] not in already_seen
            and age_hours(v.get("publishedAt"), now) <= lookback
        ][:max_videos]

        creator_max_segments = int(creator.get("maxSegmentsPerVideo", default_max_segments))
        for video in recent:
            processed_videos.append(video["videoId"])
            transcript = fetch_transcript(video["videoId"])
            description = video.get("description") or ""
            all_links = [u.rstrip(".,)") for u in URL_RE.findall(description)]
            primary_links = [u for u in all_links if is_primary_domain(u, primary_domains)]
            chapters = chapters_from_description(description)
            segments: list[dict[str, Any]] = []
            segment_method = "whole_video"

            if len(chapters) >= 2:
                segment_method = "chapters"
                for i, chapter in enumerate(chapters[:creator_max_segments]):
                    next_start = chapters[i + 1]["start"] if i + 1 < len(chapters) else None
                    segments.append(
                        {
                            "start": chapter["start"],
                            "title": chapter["title"],
                            "text": transcript_excerpt(transcript, chapter["start"], next_start),
                        }
                    )

            if not segments:
                transition_based = transition_segments(transcript, creator_max_segments)
                if transition_based:
                    segment_method = "transcript_transitions"
                    segments = transition_based

            if not segments:
                segments = [{
                    "start": 0,
                    "title": video["title"],
                    "text": transcript_excerpt(transcript, 0, None),
                }]

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
                            "segmentMethod": segment_method,
                            "discoveryWeight": creator["discoveryWeight"],
                            "primaryLinksInDescription": len(primary_links),
                        },
                        creator={
                            "name": creator["name"],
                            "handle": creator["handle"],
                            "category": creator["category"],
                            "videoTitle": video["title"],
                            "videoUrl": video["url"],
                        },
                        primary_urls=[],
                        primary_verified=False,
                        signals=["creator-radar", creator["category"], "creator-mention"],
                        related_urls=primary_links,
                    )
                )
    return out, processed_videos

def technical_core(candidate: dict[str, Any]) -> bool:
    kind = candidate.get("sourceKind")
    if kind in {"github_repo", "huggingface_model"}:
        return True
    text = f"{candidate.get('title','')} {candidate.get('summary','')}"
    if HARD_EXCLUDE_RE.search(text):
        return False
    source_name = str(candidate.get("sourceName", "")).lower()
    if candidate.get("sourceKind") == "news_search" and any(bad in source_name for bad in LOW_SIGNAL_NEWS_SOURCES):
        return False
    if candidate.get("sourceKind") in {"news_search", "hacker_news"} and str(candidate.get("title", "")).count(";") >= 2:
        return False

    ts = tokens(text)
    if ts & TECHNICAL_CUES:
        return True

    # Market/business stories are allowed only when they concern one of the
    # configured AI/Big-Tech/consulting entities and include a concrete market
    # catalyst. This keeps generic finance chatter out of Orbdev.
    if candidate.get("lane") == "market_business":
        lowered = text.lower()
        entity_match = any(
            re.search(r"(?<![a-z0-9])" + re.escape(name) + r"(?![a-z0-9])", lowered)
            for name in MARKET_ENTITY_NAMES
        )
        market_match = bool(ts & MARKET_CUES)
        if entity_match and market_match:
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
        publisher_bonus = float(metrics.get("publisherBonus", 0))
        primary_bonus = 0.35 if metrics.get("primaryPublisher") else 0.0
        return min(10.0, 5.0 + fresh + publisher_bonus + primary_bonus)

    if kind == "github_repo":
        stars = float(metrics.get("stars", 0))
        velocity = float(metrics.get("starsPerHour", 0))
        momentum = min(2.35, math.log10(stars + 1) * 0.68)
        velocity_score = min(1.65, math.log10(velocity + 1) * 0.82)
        return min(10.0, 3.0 + fresh * 0.5 + momentum + velocity_score)

    if kind == "github_trending":
        stars = float(metrics.get("stars", 0))
        per_day = float(metrics.get("starsPerDay", metrics.get("starsRecent", 0)))
        recent_score = min(2.7, math.log10(per_day + 1) * 1.15)
        total_score = min(1.0, math.log10(stars + 1) * 0.24)
        return min(10.0, 4.0 + fresh * 0.55 + recent_score + total_score)

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
            3.6
            + fresh * 0.55
            + min(math.log10(likes + 1) * 0.65, 1.5)
            + min(math.log10(downloads + 1) * 0.35, 1.5)
            + min(trending / 20, 1.0),
        )

    if kind == "creator_video_topic":
        weight = float(metrics.get("discoveryWeight", 1.0))
        method = str(metrics.get("segmentMethod", "whole_video"))
        segmentation_bonus = 0.22 if method == "chapters" else (0.08 if method == "transcript_transitions" else -0.18)
        source_link_bonus = 0.10 if int(metrics.get("primaryLinksInDescription", 0)) > 0 else 0.0
        return min(10.0, 5.05 + fresh * 0.8 + (weight - 1.0) * 2.0 + segmentation_bonus + source_link_bonus)

    return min(10.0, 4.0 + fresh)

def canonical_urls(candidate: dict[str, Any]) -> set[str]:
    urls = {str(candidate.get("url", "")).split("#", 1)[0].rstrip("/")}
    urls.update(str(url).split("#", 1)[0].rstrip("/") for url in candidate.get("primaryUrls", []) if url)
    return {url for url in urls if url and "youtube.com/watch" not in url and "news.google.com/" not in url}


def title_terms(candidate: dict[str, Any]) -> set[str]:
    return tokens(str(candidate.get("title", "")))


def similarity(a: dict[str, Any], b: dict[str, Any]) -> float:
    # Exact underlying targets are the strongest cross-lane dedupe signal.
    if canonical_urls(a) & canonical_urls(b):
        return 1.0

    ta = title_terms(a)
    tb = title_terms(b)
    if not ta or not tb:
        return 0.0

    common = ta & tb
    if not common:
        return 0.0
    base = len(common) / min(len(ta), len(tb))

    generic = WEAK_CLUSTER_TOKENS | {
        "hardware","software","platform","local","opensource","open-weight","openweight",
        "coding","runtime","inference","framework","launches","launch","unveils","adds",
        "ships","gets","using","better","faster","free","major","best","powerful","latest",
        "public","available","support","supports","serverless","preview","links"
    }
    distinctive = {token for token in common if token not in generic and len(token) >= 4}
    version_like = {
        token for token in distinctive
        if any(ch.isdigit() for ch in token) or "-" in token or "." in token
    }

    # Require either substantial title overlap, a shared version/model identifier,
    # or at least two distinctive named terms. One generic/company term is not enough.
    if base >= 0.62:
        return base
    if version_like:
        return max(base, 0.72)
    if len(distinctive) >= 2:
        return max(base, 0.68)
    return 0.0


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
        if best_index >= 0 and best_score >= 0.62:
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


def cluster_quality_gate(cluster: list[dict[str, Any]], config: dict[str, Any]) -> tuple[bool, str]:
    if not cluster:
        return False, "empty"

    lanes = {c.get("lane") for c in cluster}
    sources = {c.get("sourceName") for c in cluster if c.get("sourceName")}
    kinds = {c.get("sourceKind") for c in cluster}

    # Independent convergence is strong enough to let niche stories through even
    # when no single metric is huge.
    if len(lanes) >= 2 or len(sources) >= 2:
        return True, "independent-convergence"

    gates = config.get("qualificationGates") or {}
    best = max(cluster, key=lambda c: float(c.get("rawScore", 0)))
    kind = best.get("sourceKind")
    metrics = best.get("metrics") or {}

    if kind == "github_repo":
        stars = float(metrics.get("stars", 0))
        velocity = float(metrics.get("starsPerHour", 0))
        min_stars = float(gates.get("githubStandaloneMinStars", 120))
        min_velocity = float(gates.get("githubStandaloneMinStarsPerHour", 8))
        passed = stars >= min_stars or velocity >= min_velocity
        return passed, f"github-stars={int(stars)}-velocity={velocity:.1f}"

    if kind == "github_trending":
        per_day = float(metrics.get("starsPerDay", metrics.get("starsRecent", 0)))
        stars = float(metrics.get("stars", 0))
        min_per_day = float(gates.get("githubTrendingMinStarsPerDay", 25))
        passed = per_day >= min_per_day
        return passed, f"github-trending-stars-per-day={per_day:.1f}-total={int(stars)}"

    if kind == "huggingface_model":
        likes = float(metrics.get("likes", 0))
        downloads = float(metrics.get("downloads", 0))
        trending = float(metrics.get("trendingScore", 0))
        passed = (
            likes >= float(gates.get("huggingFaceStandaloneMinLikes", 20))
            or downloads >= float(gates.get("huggingFaceStandaloneMinDownloads", 5000))
            or trending >= float(gates.get("huggingFaceStandaloneMinTrendingScore", 10))
        )
        return passed, f"hf-likes={int(likes)}-downloads={int(downloads)}-trend={trending:.1f}"

    if kind == "creator_video_topic":
        weight = float(metrics.get("discoveryWeight", 1.0))
        method = str(metrics.get("segmentMethod", "whole_video"))
        min_weight = float(gates.get("creatorStandaloneMinWeight", 1.2))
        specific = len(title_terms(best)) >= int(gates.get("creatorStandaloneMinTitleTerms", 1))
        passed = weight >= min_weight and specific and method != "whole_video"
        return passed, f"creator-weight={weight:.2f}-method={method}"

    if kind == "hacker_news":
        points = float(metrics.get("points", 0))
        comments = float(metrics.get("comments", 0))
        min_points = float(gates.get("hackerNewsStandaloneMinPoints", 55))
        min_comments = float(gates.get("hackerNewsStandaloneMinComments", 18))
        passed = points >= min_points or comments >= min_comments
        return passed, f"hn-points={int(points)}-comments={int(comments)}"

    if kind == "news_search":
        # Major-news candidates already need to clear the stricter score. Trusted
        # publishers and primary-publisher signals receive score bonuses upstream.
        return True, "major-news-score-gate"

    return len(kinds) > 1, "mixed-evidence"

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

    if any(c["sourceKind"] == "github_trending" for c in cluster):
        score += float(heat["githubTrending"])
    elif any(
        c["sourceKind"] == "github_repo" and float((c.get("metrics") or {}).get("starsPerHour", 0)) >= 8
        for c in cluster
    ):
        score += float(heat["githubMomentum"])

    if any(c["sourceKind"] == "hacker_news" for c in cluster):
        score += float(heat["hackerNews"])
    if any(c["sourceKind"] == "huggingface_model" for c in cluster):
        score += float(heat["huggingFaceTrending"])
    if creators:
        score += float(heat["creatorMention"])

    score = round(min(10.0, score), 2)
    covered = already_covered(cluster, covered_fps)
    primary_urls = sorted({u for c in cluster for u in c.get("primaryUrls", []) if u})
    related_urls = sorted({u for c in cluster for u in c.get("relatedUrls", []) if u})
    primary_verified = any(bool(c.get("primaryVerified")) for c in cluster)
    quality_gate_passed, quality_gate = cluster_quality_gate(cluster, config)
    qualifies = (
        score >= float(config["qualificationScore"])
        and not covered
        and quality_gate_passed
    )

    return {
        "clusterId": hashlib.sha1("|".join(sorted(c["id"] for c in cluster)).encode()).hexdigest()[:16],
        "title": best["title"],
        "score": score,
        "qualifiesForEditorial": qualifies,
        "publishReady": False,
        "primarySourceAvailable": bool(primary_urls) or primary_verified,
        "needsPrimaryVerification": qualifies and not primary_verified,
        "needsEditorialVerification": qualifies,
        "qualityGatePassed": quality_gate_passed,
        "qualityGate": quality_gate,
        "alreadyCovered": covered,
        "lanes": lanes,
        "creatorCategories": creator_categories,
        "creators": creators,
        "sourceNames": sources,
        "primaryUrls": primary_urls,
        "relatedUrls": related_urls,
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
    if config.get("marketBusiness"):
        candidates.extend(
            google_news_candidates(
                config,
                now,
                section="marketBusiness",
                lane="market_business",
                signal="market-business-search",
            )
        )
    candidates.extend(github_candidates(config, now))
    candidates.extend(github_trending_candidates(config, now))
    candidates.extend(hacker_news_candidates(config, now))
    candidates.extend(huggingface_candidates(config, now))
    backfill_mode = bool(config.get("backfillMode", False))
    seen_creator_videos = set() if backfill_mode else set(old_state.get("seenCreatorVideos") or [])
    if backfill_mode:
        print("Backfill mode: ignoring prior creator seen-state for historical discovery")
    creator_items, seen_videos = creator_candidates(config, now, seen_creator_videos)
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
    for lane in ("major_news", "market_business", "hot_emerging", "creator_radar"):
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
