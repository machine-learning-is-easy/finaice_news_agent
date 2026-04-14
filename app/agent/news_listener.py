"""
NewsListener — continuously polls RSS feeds, analyzes new articles,
and sends an email for each significant event.

Designed to run without a database (uses in-memory deduplication).
"""
import time
import hashlib
from datetime import datetime, timezone

from app.ingestion.rss_fetcher import RSSFetcher
from app.events.extractor import EventExtractor
from app.agent.reasoning_agent import ReasoningAgent
from app.agent.scoring_agent import ScoringAgent
from app.market.context_builder import MarketContextBuilder
from app.delivery.email_sender import EmailSender
from app.agent.schemas import NewsArticle
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Default RSS feeds used when none are configured in .env
_DEFAULT_FEEDS = [
    "https://feeds.reuters.com/reuters/businessNews",
    "https://feeds.reuters.com/reuters/technologyNews",
    "https://finance.yahoo.com/news/rssindex",
]


def _article_hash(article: NewsArticle) -> str:
    raw = f"{article.title}||{article.source_url or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()


class NewsListener:
    def __init__(
        self,
        recipient_email: str,
        poll_interval: int = 300,
        feed_urls: list[str] | None = None,
        min_score: float | None = None,
    ):
        self.recipient      = recipient_email
        self.poll_interval  = poll_interval
        self.feed_urls      = feed_urls or settings.rss_feed_list or _DEFAULT_FEEDS
        self.min_score      = min_score if min_score is not None else settings.alert_impact_threshold

        self.fetcher        = RSSFetcher(self.feed_urls)
        self.extractor      = EventExtractor()
        self.scorer         = ScoringAgent()
        self.reasoner       = ReasoningAgent()
        self.market_builder = MarketContextBuilder()
        self.email_sender   = EmailSender(recipient=recipient_email)

        self._seen: set[str] = set()   # in-memory dedup
        self._running = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def start(self) -> None:
        self._running = True
        feeds_display = "\n  ".join(self.feed_urls)
        print(f"\n[Agent] Listening to {len(self.feed_urls)} feed(s):")
        print(f"  {feeds_display}")
        print(f"[Agent] Poll interval : {self.poll_interval}s")
        print(f"[Agent] Min score     : {self.min_score}")
        print(f"[Agent] Alerts → {self.recipient}")
        print("[Agent] Press Ctrl+C to stop.\n")

        try:
            while self._running:
                self._poll_once()
                self._wait()
        except KeyboardInterrupt:
            print("\n[Agent] Stopped by user.")

    def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _poll_once(self) -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        print(f"[{now}] Fetching news...", flush=True)

        articles = self.fetcher.fetch_all()
        new_count = 0

        for article in articles:
            h = _article_hash(article)
            if h in self._seen:
                continue
            self._seen.add(h)
            new_count += 1
            self._process(article)

        print(f"[{now}] {len(articles)} articles fetched, {new_count} new.", flush=True)

    def _process(self, article: NewsArticle) -> None:
        try:
            # Step 1: extract structured event
            event = self.extractor.extract(article)

            # Step 2: quick score — skip low-signal articles (no LLM cost)
            market_context = None
            if event.primary_ticker:
                try:
                    market_context = self.market_builder.build(event.primary_ticker)
                except Exception:
                    pass

            score = self.scorer.score(event, market_context)

            if not self.scorer.should_run_full_analysis(score, threshold=self.min_score):
                logger.debug(
                    "listener.skipped_low_score",
                    title=article.title[:60],
                    score=score,
                )
                return

            # Step 3: full LLM reasoning
            print(
                f"  → [{event.event_type.upper()}] {article.title[:70]} "
                f"(score={score:.2f}, ticker={event.primary_ticker or 'N/A'})",
                flush=True,
            )

            analysis = self.reasoner.analyze(
                article=article,
                event=event,
                market_context=market_context,
                similar_events=[],   # no DB in listener mode
            )

            # Step 4: send email
            sent = self.email_sender.send(event, analysis)
            status = "Email sent" if sent else "Email FAILED"
            print(
                f"  ✓ {status} — {analysis.final_label.upper()} "
                f"({analysis.final_score:.0%}) | {analysis.user_readable_summary[:80]}",
                flush=True,
            )

        except Exception as e:
            logger.error("listener.process_error", title=article.title[:60], error=str(e))

    def _wait(self) -> None:
        print(f"[Agent] Next check in {self.poll_interval}s...\n", flush=True)
        time.sleep(self.poll_interval)
