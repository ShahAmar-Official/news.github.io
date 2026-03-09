"""
news_sources.py — Fetch top news stories from Google News RSS, NewsAPI, Google Trends,
and Hacker News.

NewsAPI is the PRIMARY source for this news channel. Google News RSS is the
secondary free source. Returns a deduplicated list of news story strings and
picks the best story using a cross-source scoring heuristic that heavily
prioritises NewsAPI and Google News RSS results.
"""

import logging
import random
import time
import xml.etree.ElementTree as ET
from typing import Any

import requests

import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_MIN_TOPICS = 10  # Minimum number of topics to maintain in the combined list

# ---------------------------------------------------------------------------
# Fallback topics used when all external sources fail
# ---------------------------------------------------------------------------
FALLBACK_TOPICS: list[str] = [
    "Global economic outlook",
    "Climate change policy updates",
    "AI regulation developments",
    "Space mission updates",
    "Healthcare breakthroughs",
    "Cybersecurity threats",
    "Geopolitical tensions",
    "Renewable energy milestones",
    "Stock market analysis",
    "Supreme Court rulings",
]


def _fetch_google_news_rss(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch top headlines from Google News RSS feed.

    Uses the public Google News RSS endpoint — completely free, no API key
    required. Returns news headlines suitable for short-form news content.
    """
    url = "https://news.google.com/rss"
    params = {"hl": "en-US", "gl": "US", "ceid": "US:en"}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            # Python 3.7.1+ stdlib XML parser does not resolve external entities
            # and has built-in protection against entity expansion attacks.
            root = ET.fromstring(resp.text)
            topics: list[str] = []
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    # Strip source suffix like "Title - Source Name" to keep clean headline
                    headline = title_el.text.strip()
                    if " - " in headline:
                        headline = headline.rsplit(" - ", 1)[0].strip()
                    if headline:
                        topics.append(headline)
            logger.info("Google News RSS returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google News RSS attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def _fetch_google_trends(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch daily trending searches for the US from Google Trends RSS feed.

    Uses the public Google Trends RSS endpoint — focuses on news-relevant
    trending searches. More reliable than the unofficial pytrends scraping library.
    """
    url = "https://trends.google.com/trending/rss?geo=US"

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.text)
            topics: list[str] = []
            for item in root.iter("item"):
                title_el = item.find("title")
                if title_el is not None and title_el.text:
                    topics.append(title_el.text.strip())
            logger.info("Google Trends RSS returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Google Trends RSS attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def _fetch_hackernews_trending(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch top story titles from Hacker News via the Algolia API.

    Completely free — no API key or authentication required.  The Algolia
    search API for Hacker News returns current front-page stories in a
    single request.
    """
    url = "https://hn.algolia.com/api/v1/search"
    params = {"tags": "front_page", "hitsPerPage": 25}

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()
            hits = data.get("hits", [])
            topics = [hit["title"] for hit in hits if hit.get("title")]
            logger.info("Hacker News returned %d topics", len(topics))
            return topics[:20]
        except Exception as exc:  # noqa: BLE001
            logger.warning("Hacker News attempt %d/%d failed: %s", attempt, retries, exc)
            if attempt < retries:
                time.sleep(backoff * attempt)
    return []


def _fetch_newsapi_trending(retries: int = 3, backoff: float = 2.0) -> list[str]:
    """Fetch top headline titles from NewsAPI.org — the PRIMARY news source.

    Fetches from multiple news categories defined in ``config.NEWS_CATEGORIES``
    to ensure broad coverage of breaking news across all major topics.
    ``NEWSAPI_KEY`` is required for this news channel; logs an error if absent.
    """
    if not config.NEWSAPI_KEY:
        logger.error(
            "NEWSAPI_KEY is not set — this is required for the news channel. "
            "Set the NEWSAPI_KEY secret in your GitHub repository settings."
        )
        return []

    categories = getattr(config, "NEWS_CATEGORIES", ["general"])
    all_topics: list[str] = []
    seen: set[str] = set()

    for category in categories:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "country": "us",
            "category": category,
            "pageSize": 10,
            "apiKey": config.NEWSAPI_KEY,
        }

        for attempt in range(1, retries + 1):
            try:
                resp = requests.get(url, params=params, timeout=15)
                resp.raise_for_status()
                articles = resp.json().get("articles", [])
                for a in articles:
                    if not a.get("title") or a["title"] == "[Removed]":
                        continue
                    # Strip source suffix like "Title - Source Name"
                    headline = a["title"].split(" - ")[0].strip()
                    key = headline.lower()
                    if headline and key not in seen:
                        seen.add(key)
                        all_topics.append(headline)
                logger.info("NewsAPI [%s] returned %d articles", category, len(articles))
                break
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "NewsAPI [%s] attempt %d/%d failed: %s", category, attempt, retries, exc
                )
                if attempt < retries:
                    time.sleep(backoff * attempt)

    logger.info("NewsAPI total unique topics across all categories: %d", len(all_topics))
    return all_topics[:40]


def get_trending_topics() -> list[str]:
    """Combine all news sources into a deduplicated list.

    NewsAPI and Google News RSS are weighted 3x as they are the primary news
    sources. Returns at least 10 topic strings, falling back to
    :data:`FALLBACK_TOPICS` if the external sources cannot provide enough results.
    """
    newsapi_topics = _fetch_newsapi_trending()
    google_news_topics = _fetch_google_news_rss()
    google_trends_topics = _fetch_google_trends()
    hn_topics = _fetch_hackernews_trending()

    seen: set[str] = set()
    combined: list[str] = []
    # Primary sources first (3x weight means they appear first in the combined list)
    for topic in newsapi_topics + google_news_topics + google_trends_topics + hn_topics:
        normalised = topic.strip()
        if normalised and normalised.lower() not in seen:
            seen.add(normalised.lower())
            combined.append(normalised)

    if len(combined) < _MIN_TOPICS:
        logger.info("Fewer than %d topics found (%d); padding with fallbacks", _MIN_TOPICS, len(combined))
        for fallback in FALLBACK_TOPICS:
            if fallback.lower() not in seen:
                seen.add(fallback.lower())
                combined.append(fallback)
            if len(combined) >= _MIN_TOPICS:
                break

    logger.info("Total unique news topics available: %d", len(combined))
    return combined


def get_top_news_story() -> str:
    """Pick the most newsworthy story using a cross-source scoring heuristic.

    Fetches from each source once, then scores topics so that those appearing
    in multiple sources rank higher. NewsAPI and Google News RSS results receive
    a 3x weight multiplier as the primary news sources, ensuring breaking news
    from verified outlets consistently tops the selection.
    """
    newsapi_topics = _fetch_newsapi_trending()
    google_news_topics = _fetch_google_news_rss()
    google_trends_topics = _fetch_google_trends()
    hn_topics = _fetch_hackernews_trending()

    scores: dict[str, float] = {}

    # NewsAPI — 3x weight (primary news source)
    for rank, topic in enumerate(newsapi_topics):
        key = topic.strip().lower()
        scores[key] = scores.get(key, 0) + 3.0 * (len(newsapi_topics) - rank)

    # Google News RSS — 3x weight (primary free news source)
    for rank, topic in enumerate(google_news_topics):
        key = topic.strip().lower()
        bonus = 2.0 if key in scores else 1.0
        scores[key] = scores.get(key, 0) + 3.0 * bonus * (len(google_news_topics) - rank)

    # Google Trends — 1x weight (supplementary signal)
    for rank, topic in enumerate(google_trends_topics):
        key = topic.strip().lower()
        bonus = 2.0 if key in scores else 1.0
        scores[key] = scores.get(key, 0) + bonus * (len(google_trends_topics) - rank)

    # Hacker News — 1x weight (supplementary tech/science signal)
    for rank, topic in enumerate(hn_topics):
        key = topic.strip().lower()
        bonus = 2.0 if key in scores else 1.0
        scores[key] = scores.get(key, 0) + bonus * (len(hn_topics) - rank)

    # Rebuild mapping from lower-case key → original casing
    original: dict[str, str] = {}
    all_topics = newsapi_topics + google_news_topics + google_trends_topics + hn_topics
    for topic in all_topics:
        key = topic.strip().lower()
        if key not in original:
            original[key] = topic.strip()

    if not scores:
        logger.warning("No news stories found; using random fallback topic")
        return random.choice(FALLBACK_TOPICS)

    # Pick randomly from the top scoring topics (up to 5) to ensure variety across runs
    sorted_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    top_keys = sorted_keys[:min(5, len(sorted_keys))]
    best_key = random.choice(top_keys)
    best_topic = original.get(best_key, FALLBACK_TOPICS[0])
    logger.info(
        "News story selected: '%s' (score=%.1f, from top %d)",
        best_topic, scores[best_key], len(top_keys),
    )

    # Pad the combined topic list with fallbacks for consistency
    seen: set[str] = {t.strip().lower() for t in all_topics}
    combined = list(original.values())
    for fallback in FALLBACK_TOPICS:
        if fallback.lower() not in seen:
            seen.add(fallback.lower())
            combined.append(fallback)
        if len(combined) >= _MIN_TOPICS:
            break
    logger.info("Total unique news topics available: %d", len(combined))

    return best_topic
