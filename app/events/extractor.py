from app.agent.schemas import NewsArticle, ExtractedEvent, EntityMention
from app.entity.ticker_linker import TickerLinker
from app.events.classifier import EventClassifier
from app.events.sentiment import SentimentAnalyzer
from app.events.novelty import score_novelty
from app.core.logging import get_logger

logger = get_logger(__name__)

_TIME_HORIZON_MAP: dict[str, str] = {
    "earnings": "1d-3d",
    "guidance": "1w-1m",
    "regulation": "1w-1m",
    "merger": "long_term",
    "product_launch": "1w-1m",
    "analyst_action": "intraday",
    "management_change": "1d-3d",
    "macro_data": "intraday",
    "buyback": "1d-3d",
    "lawsuit": "1d-3d",
    "other": "1d-3d",
}


class EventExtractor:
    def __init__(self):
        self.ticker_linker = TickerLinker()
        self.classifier = EventClassifier()
        self.sentiment = SentimentAnalyzer()

    def extract(self, article: NewsArticle) -> ExtractedEvent:
        full_text = article.title + "\n" + article.content

        entities = self.ticker_linker.link(full_text)
        classification = self.classifier.predict(article.title, article.content)
        sentiment = self.sentiment.predict(article.title, article.content)
        novelty = score_novelty(article.title, article.content)

        primary_ticker = self._pick_primary_ticker(entities)
        impact_direction = self._map_direction(classification.label, sentiment.label)
        impact_strength = round(0.5 * sentiment.score + 0.5 * novelty, 4)
        time_horizon = _TIME_HORIZON_MAP.get(classification.label, "1d-3d")
        confidence = round(min(classification.confidence, sentiment.confidence) * 0.9 + 0.1, 4)

        event = ExtractedEvent(
            article_id=article.id or 0,
            primary_ticker=primary_ticker,
            event_type=classification.label,
            event_subtype=classification.subtype,
            sentiment_label=sentiment.label,
            sentiment_score=round(sentiment.score, 4),
            relevance_score=self._estimate_relevance(entities, classification.confidence),
            novelty_score=novelty,
            impact_direction=impact_direction,
            impact_strength=impact_strength,
            time_horizon=time_horizon,
            confidence=confidence,
            fact_summary=self._build_summary(article, classification.label),
            entities=entities,
        )

        logger.info(
            "event_extractor.done",
            ticker=primary_ticker,
            event_type=classification.label,
            sentiment=sentiment.label,
            impact=impact_direction,
        )
        return event

    def _pick_primary_ticker(self, entities: list[EntityMention]) -> str | None:
        for ent in entities:
            if ent.role == "primary_subject" and ent.ticker:
                return ent.ticker
        return None

    def _map_direction(self, event_type: str, sentiment_label: str) -> str:
        # Buyback is structurally positive regardless of sentiment
        if event_type == "buyback":
            return "positive"
        # Lawsuits are structurally negative
        if event_type == "lawsuit":
            return "negative"
        return {"positive": "positive", "negative": "negative"}.get(sentiment_label, "neutral")

    def _estimate_relevance(self, entities: list[EntityMention], event_confidence: float) -> float:
        entity_boost = min(0.2, len(entities) * 0.05)
        return round(min(1.0, event_confidence + entity_boost), 4)

    def _build_summary(self, article: NewsArticle, event_type: str) -> str:
        return f"[{event_type.upper()}] {article.title}"
