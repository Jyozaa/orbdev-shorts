from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import discover_news as d


def c(lane: str, kind: str, title: str, url: str, summary: str = "", source: str = "test"):
    return d.make_candidate(lane, kind, title, url, "2026-10-04T00:00:00Z", source, summary)


def main() -> None:
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

    print("Discovery logic regression checks passed")


if __name__ == "__main__":
    main()
