"""
Unit tests for the pipeline's pure-Python components (no DB, no LLM calls).
"""
from datetime import datetime, timezone

import pytest

from app.agent.schemas import NewsArticle
from app.events.extractor import EventExtractor
from app.events.classifier import EventClassifier
from app.events.sentiment import SentimentAnalyzer
from app.events.novelty import score_novelty
from app.entity.ticker_linker import TickerLinker
from app.agent.scoring_agent import ScoringAgent


def make_article(title: str, content: str) -> NewsArticle:
    return NewsArticle(
        id=1,
        source="test",
        title=title,
        content=content,
        published_at=datetime.now(timezone.utc),
    )


class TestEventClassifier:
    def test_earnings_beat(self):
        clf = EventClassifier()
        result = clf.predict("Apple beats earnings estimates", "Apple beat expectations for Q2")
        assert result.label == "earnings"
        assert result.confidence >= 0.5

    def test_regulation(self):
        clf = EventClassifier()
        result = clf.predict("FTC fines Meta $1B for antitrust violations", "regulatory action")
        assert result.label == "regulation"

    def test_merger(self):
        clf = EventClassifier()
        result = clf.predict("Microsoft acquires Activision in $69B deal", "deal to acquire gaming company")
        assert result.label == "merger"

    def test_analyst_downgrade(self):
        clf = EventClassifier()
        result = clf.predict("Goldman Sachs downgraded Tesla to neutral", "downgraded to underperform")
        assert result.label == "analyst_action"
        assert result.subtype == "downgrade"


class TestSentimentAnalyzer:
    def test_positive_sentiment(self):
        sa = SentimentAnalyzer()
        result = sa.predict("NVIDIA earnings beat expectations with record revenue", "profit rose significantly")
        assert result.label == "positive"
        assert result.score > 0.5

    def test_negative_sentiment(self):
        sa = SentimentAnalyzer()
        result = sa.predict("Company missed estimates, guidance lowered", "disappointing results")
        assert result.label == "negative"

    def test_neutral_baseline(self):
        sa = SentimentAnalyzer()
        result = sa.predict("Company scheduled board meeting", "routine quarterly review")
        assert result.label == "neutral"


class TestTickerLinker:
    def test_explicit_ticker_symbol(self):
        tl = TickerLinker()
        results = tl.link("$AAPL reported strong earnings today")
        tickers = [m.ticker for m in results]
        assert "AAPL" in tickers

    def test_company_name_alias(self):
        tl = TickerLinker()
        results = tl.link("Nvidia launched new AI chips")
        tickers = [m.ticker for m in results]
        assert "NVDA" in tickers

    def test_primary_role(self):
        tl = TickerLinker()
        results = tl.link("Apple beat earnings, Google also mentioned")
        primary = next((m for m in results if m.role == "primary_subject"), None)
        assert primary is not None

    def test_empty_text(self):
        tl = TickerLinker()
        results = tl.link("No companies mentioned here at all")
        assert isinstance(results, list)


class TestNoveltyScorer:
    def test_high_novelty_signals(self):
        score = score_novelty("Record-breaking earnings surprise shocks Wall Street", "unprecedented results")
        assert score > 0.5

    def test_low_novelty_signals(self):
        score = score_novelty("Results in line with consensus forecast as expected", "widely anticipated results")
        assert score < 0.5


class TestEventExtractor:
    def test_full_extraction(self):
        extractor = EventExtractor()
        article = make_article(
            "NVIDIA beats Q3 earnings, raises guidance",
            "NVIDIA ($NVDA) reported Q3 earnings that beat estimates. The company also raised its full-year guidance."
        )
        event = extractor.extract(article)
        assert event.event_type in ("earnings", "guidance")
        assert event.primary_ticker == "NVDA"
        assert event.sentiment_label == "positive"
        assert 0.0 <= event.confidence <= 1.0

    def test_negative_event(self):
        extractor = EventExtractor()
        article = make_article(
            "Tesla issued lawsuit settlement warning",
            "Tesla ($TSLA) faces a class action lawsuit and warned of potential settlement costs."
        )
        event = extractor.extract(article)
        assert event.event_type == "lawsuit"
        assert event.impact_direction == "negative"


class TestScoringAgent:
    def test_high_impact_score(self):
        from app.agent.schemas import ExtractedEvent
        scorer = ScoringAgent()
        event = ExtractedEvent(
            article_id=1,
            primary_ticker="NVDA",
            event_type="earnings",
            sentiment_label="positive",
            sentiment_score=0.9,
            relevance_score=0.9,
            novelty_score=0.85,
            impact_direction="positive",
            impact_strength=0.85,
            time_horizon="1d-3d",
            confidence=0.9,
            fact_summary="NVDA beats earnings",
        )
        score = scorer.score(event, market_context=None)
        assert score >= 0.7
        assert scorer.should_run_full_analysis(score)
