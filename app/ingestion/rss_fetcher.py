"""
RSS feed ingestion.
Fetches and parses RSS/Atom feeds into NewsArticle objects.
"""
from datetime import datetime, timezone
from typing import AsyncGenerator

import feedparser
import httpx

from app.agent.schemas import NewsArticle
from app.ingestion.cleaner import clean_article_text, truncate
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed"):
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    return datetime.now(timezone.utc)


def _entry_to_article(entry, feed_url: str) -> NewsArticle | None:
    title = getattr(entry, "title", "").strip()
    if not title:
        return None

    content_raw = ""
    # Try content first, then summary
    if hasattr(entry, "content") and entry.content:
        content_raw = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        content_raw = entry.summary or ""

    content = truncate(clean_article_text(content_raw), max_chars=6000)
    link = getattr(entry, "link", None)
    source = feed_url.split("/")[2] if "/" in feed_url else feed_url

    return NewsArticle(
        source=source,
        title=title,
        content=content,
        source_url=link,
        published_at=_parse_date(entry),
        language="en",
    )


class RSSFetcher:
    def __init__(self, feed_urls: list[str] | None = None):
        self.feed_urls = feed_urls or settings.rss_feed_list

    def fetch_all(self) -> list[NewsArticle]:
        articles = []
        for url in self.feed_urls:
            articles.extend(self.fetch_feed(url))
        return articles

    def fetch_feed(self, url: str) -> list[NewsArticle]:
        logger.info("rss_fetcher.fetching", url=url)
        try:
            feed = feedparser.parse(url)
            results = []
            for entry in feed.entries:
                article = _entry_to_article(entry, url)
                if article:
                    results.append(article)
            logger.info("rss_fetcher.done", url=url, count=len(results))
            return results
        except Exception as e:
            logger.error("rss_fetcher.error", url=url, error=str(e))
            return []
