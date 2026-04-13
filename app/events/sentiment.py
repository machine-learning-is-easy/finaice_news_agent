"""
Sentiment analysis for financial text.
Uses keyword heuristics in Phase 1.
Designed to be swapped with FinBERT in Phase 2.
"""
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class SentimentResult:
    label: str  # positive, negative, neutral
    score: float
    confidence: float


_POSITIVE_WORDS = [
    "beat", "exceeded", "surpassed", "record", "growth", "profit", "gain",
    "upgrade", "outperform", "bullish", "raised guidance", "strong demand",
    "revenue growth", "margin expansion", "better than expected", "above consensus",
    "increased dividend", "buyback", "approval", "launch", "partnership",
    "higher", "rose", "soared", "jumped", "rallied",
]

_NEGATIVE_WORDS = [
    "miss", "missed", "below expectations", "disappointing", "loss", "decline",
    "downgrade", "underperform", "bearish", "lowered guidance", "warning",
    "cut", "reduced", "fell", "dropped", "plunged", "slipped", "tumbled",
    "fine", "penalty", "lawsuit", "probe", "sanction", "tariff",
    "layoffs", "restructuring", "write-down", "impairment",
]


class SentimentAnalyzer:
    def predict(self, title: str, content: str) -> SentimentResult:
        combined = (title + " " + content[:800]).lower()

        pos_hits = sum(1 for w in _POSITIVE_WORDS if w in combined)
        neg_hits = sum(1 for w in _NEGATIVE_WORDS if w in combined)

        total = pos_hits + neg_hits
        if total == 0:
            return SentimentResult(label="neutral", score=0.5, confidence=0.4)

        if pos_hits > neg_hits:
            raw = pos_hits / total
            score = 0.5 + 0.5 * raw
            label = "positive"
        elif neg_hits > pos_hits:
            raw = neg_hits / total
            score = 0.5 + 0.5 * raw
            label = "negative"
        else:
            score = 0.5
            label = "neutral"

        # Confidence grows with number of signal words
        confidence = min(0.95, 0.4 + total * 0.05)
        logger.debug("sentiment.result", label=label, score=score, pos=pos_hits, neg=neg_hits)
        return SentimentResult(label=label, score=round(score, 4), confidence=round(confidence, 4))
