"""
Backfill script: fetch RSS feeds and run the full pipeline for each article.
Run from project root: python -m scripts.backfill_news
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.logging import setup_logging, get_logger
from app.db.session import AsyncSessionLocal
from app.ingestion.rss_fetcher import RSSFetcher
from app.pipeline import FinanceNewsAnalysisPipeline

setup_logging()
logger = get_logger("backfill")


async def run_backfill(feed_urls: list[str] | None = None):
    fetcher = RSSFetcher(feed_urls=feed_urls)
    articles = fetcher.fetch_all()
    logger.info("backfill.articles_fetched", count=len(articles))

    success = 0
    errors = 0

    async with AsyncSessionLocal() as db:
        pipeline = FinanceNewsAnalysisPipeline(db)
        for i, article in enumerate(articles):
            try:
                result = await pipeline.run(article)
                logger.info(
                    "backfill.processed",
                    index=i,
                    ticker=result.primary_ticker,
                    label=result.analysis.final_label,
                )
                success += 1
            except Exception as e:
                logger.error("backfill.error", index=i, title=article.title[:60], error=str(e))
                errors += 1
                await db.rollback()

    logger.info("backfill.done", success=success, errors=errors)


if __name__ == "__main__":
    asyncio.run(run_backfill())
