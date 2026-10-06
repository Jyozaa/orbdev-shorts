from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import discover_news as d


def c(lane: str, kind: str, title: str, url: str, summary: str = "", source: str = "test"):
    return d.make_candidate(lane, kind, title, url, "2026-10-04T00:00:00Z", source, summary)


def main() -> None:
    # GitHub discovery fetch_text returns (text, final_url). Creator Radar must
    # unpack that pair before parsing ytInitialData from a YouTube channel page.
    from datetime import datetime,timezone
    saved_fetch=d.fetch_text
    sample='var ytInitialData = '+__import__("json").dumps({
        "videoRenderer":{"videoId":"TESTVIDEO123","title":{"runs":[{"text":"New open model released"}]},
                         "publishedTimeText":{"simpleText":"1 day ago"}}
    })+';'
    try:
        d.fetch_text=lambda url,**kwargs:(sample,url)
        videos=d.youtube_channel_page_videos("https://youtube.com/@test",datetime(2026,10,6,tzinfo=timezone.utc),3)
        assert len(videos)==1 and videos[0]["videoId"]=="TESTVIDEO123"
    finally:
        d.fetch_text=saved_fetch
    shared_summary = "Gemini 4, GPT 6.1, Dots, Claude Sonnet 5.5, Ideogram 4.5, Flux 3: AI NEWS"
    flux = c("creator_radar", "creator_video_topic", "Flux 3", "https://youtube.com/watch?v=x&t=10s", shared_summary)
    ideogram = c("creator_radar", "creator_video_topic", "Ideogram 4.5", "https://youtube.com/watch?v=x&t=20s", shared_summary)
    assert d.similarity(flux, ideogram) == 0.0, "creator chapters from one roundup must remain separate"

    repo = c("hot_emerging", "github_repo", "Niko1221/Strata", "https://github.com/Niko1221/Strata")
    hn = c("hot_emerging", "hacker_news", "Run Qwen 3.8 Flash Next on consumer hardware", "https://github.com/Niko1221/Strata")
    assert d.similarity(repo, hn) == 1.0, "identical underlying URLs must cluster"

    astra_a = c("major_news", "news_search", "GPT-6 Astra clears World of Warcraft starting zone", "https://example.com/a")
    astra_b = c("major_news", "news_search", "ChatGPT-6 Astra plays World of Warcraft blind", "https://example.com/b")
    assert d.similarity(astra_a, astra_b) >= 0.62, "same named model/event should cluster"

    muse = c("major_news", "news_search", "Meta releases Muse hardware SDK for developers", "https://example.com/c")
    assert d.similarity(astra_a, muse) < 0.62, "unrelated technical stories must not cluster"

    finance = c(
        "major_news",
        "news_search",
        "Consumer Tech roundup: Anthropic prepares for IPO and AI stocks move",
        "https://news.google.com/example",
        source="TradingView",
    )
    assert not d.technical_core(finance), "finance/market roundups must be filtered"

    technical = c(
        "hot_emerging",
        "github_repo",
        "example/agent-runtime",
        "https://github.com/example/agent-runtime",
        "Open-source coding agent runtime",
        source="GitHub",
    )
    assert d.technical_core(technical), "open-source developer tools must survive"

    math_result = c(
        "major_news",
        "news_search",
        "Researchers prove new theorem in combinatorics",
        "https://example.com/math",
        "A new mathematical proof resolves a longstanding conjecture",
        source="Quanta Magazine",
    )
    assert d.technical_core(math_result), "new mathematical findings must survive discovery"

    cyber_incident = c(
        "major_news",
        "news_search",
        "Major cloud provider confirms data breach after zero-day attack",
        "https://example.com/cyber",
        "Confirmed cybersecurity incident exposed credentials",
        source="Reuters",
    )
    assert d.technical_core(cyber_incident), "confirmed cyber incidents must survive discovery"

    market_story = c(
        "market_business",
        "news_search",
        "Microsoft raises AI capex guidance after cloud revenue growth",
        "https://example.com/market",
        "Microsoft earnings show higher AI infrastructure spending and revenue guidance",
        source="Reuters",
    )
    assert d.technical_core(market_story), "material Big Tech market stories must survive discovery"

    generic_market = c(
        "market_business",
        "news_search",
        "Regional bank shares rise after earnings",
        "https://example.com/generic-market",
        "Stocks gained after quarterly profit",
        source="Reuters",
    )
    assert not d.technical_core(generic_market), "generic non-tech market news must stay out"

    low_repo = c(
        "hot_emerging",
        "github_repo",
        "example/tiny-new-tool",
        "https://github.com/example/tiny-new-tool",
        "Open-source developer CLI",
        source="GitHub",
    )
    low_repo["metrics"] = {"stars": 45, "starsPerHour": 2.0}
    low_repo["rawScore"] = 7.8
    gate, _ = d.cluster_quality_gate([low_repo], {
        "qualificationGates": {
            "githubStandaloneMinStars": 120,
            "githubStandaloneMinStarsPerHour": 8,
        }
    })
    assert not gate, "small standalone repos must not qualify on freshness alone"

    hot_repo = c(
        "hot_emerging",
        "github_trending",
        "example/hot-tool",
        "https://github.com/example/hot-tool",
        "Developer runtime",
        source="GitHub Trending",
    )
    hot_repo["metrics"] = {"stars": 900, "starsRecent": 170, "starsPerDay": 170, "trendingWindow": "daily"}
    gate, _ = d.cluster_quality_gate([hot_repo], {
        "qualificationGates": {
            "githubTrendingMinStarsPerDay": 25,
        }
    })
    assert gate, "GitHub Trending must support older projects with fresh momentum"

    stale_famous = c(
        "hot_emerging",
        "github_trending",
        "example/famous-but-slow",
        "https://github.com/example/famous-but-slow",
        "Popular developer tool",
        source="GitHub Trending",
    )
    stale_famous["metrics"] = {"stars": 100000, "starsRecent": 70, "starsPerDay": 10, "trendingWindow": "weekly"}
    gate, _ = d.cluster_quality_gate([stale_famous], {
        "qualificationGates": {
            "githubTrendingMinStarsPerDay": 25,
        }
    })
    assert not gate, "lifetime popularity must not substitute for current momentum"

    creator = c(
        "creator_radar",
        "creator_video_topic",
        "Interesting Agent Runtime",
        "https://youtube.com/watch?v=new",
        "New agent runtime explanation",
        source="Fireship",
    )
    creator["metrics"] = {"discoveryWeight": 1.3, "segmentMethod": "chapters"}
    gate, _ = d.cluster_quality_gate([creator], {
        "qualificationGates": {
            "creatorStandaloneMinWeight": 1.2,
            "creatorStandaloneMinTitleTerms": 1,
        }
    })
    assert gate, "high-signal creator chapters can qualify independently"

    print("Discovery logic regression checks passed")


if __name__ == "__main__":
    main()
