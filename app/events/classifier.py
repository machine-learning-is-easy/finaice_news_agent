"""
Event type classifier.
Uses keyword heuristics for Phase 1 (fast, no external dependency).
Can be replaced with a fine-tuned classifier later.
"""
import re
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ClassificationResult:
    label: str
    subtype: str | None
    confidence: float


# Rule sets: (event_type, subtype, keywords, weight)
_RULES: list[tuple[str, str | None, list[str], float]] = [
    ("earnings", "beat", ["beat estimates", "beat expectations", "topped estimates",
                          "earnings beat", "eps beat", "above consensus"], 0.9),
    ("earnings", "miss", ["missed estimates", "missed expectations", "below consensus",
                          "earnings miss", "eps miss", "disappointing earnings"], 0.9),
    ("earnings", None, ["quarterly results", "earnings report", "q1 earnings", "q2 earnings",
                        "q3 earnings", "q4 earnings", "annual results", "fiscal year results",
                        "reported earnings", "profit rose", "profit fell", "net income"], 0.75),
    ("guidance", "raised", ["raised guidance", "raised outlook", "raised forecast",
                             "raised its forecast", "increased guidance", "upside guidance"], 0.9),
    ("guidance", "lowered", ["lowered guidance", "cut guidance", "reduced guidance",
                              "warned of", "issued a warning", "downside risk"], 0.9),
    ("guidance", None, ["guidance", "outlook", "forecast", "full-year expectations",
                        "next quarter expectations"], 0.6),
    ("regulation", "fine", ["fined", "penalty", "antitrust", "regulatory action",
                             "enforcement action", "doj", "ftc", "sec charged"], 0.9),
    ("regulation", "approval", ["approved", "fda approval", "regulatory approval",
                                 "cleared by", "green light"], 0.85),
    ("regulation", None, ["regulation", "regulator", "legislation", "tariff", "sanction",
                           "export control", "ban", "compliance", "probe"], 0.7),
    ("merger", "acquisition", ["acquires", "acquisition", "buyout", "takeover bid",
                                "agreed to buy", "deal to acquire"], 0.9),
    ("merger", "merger", ["merger", "to merge", "combine with", "joint venture"], 0.85),
    ("merger", "divestiture", ["divest", "spin-off", "sell unit", "carve-out"], 0.85),
    ("product_launch", None, ["launches", "unveiled", "introduces", "new product",
                               "released", "debut", "partnership", "collaboration"], 0.7),
    ("analyst_action", "upgrade", ["upgraded", "upgrade to buy", "raised to overweight",
                                    "upgraded to outperform"], 0.9),
    ("analyst_action", "downgrade", ["downgraded", "cut to sell", "lowered to underperform",
                                      "downgraded to neutral"], 0.9),
    ("analyst_action", "price_target", ["price target", "raises pt", "cuts pt",
                                         "target price", "raised target"], 0.85),
    ("management_change", None, ["ceo", "cfo", "coo", "chief executive", "steps down",
                                  "appointed", "resigned", "board of directors", "chairman"], 0.75),
    ("macro_data", None, ["cpi", "inflation", "federal reserve", "fed rate", "interest rate",
                           "gdp", "unemployment", "jobs report", "nonfarm payroll",
                           "consumer confidence", "ppi", "pce"], 0.8),
    ("buyback", None, ["share repurchase", "buyback", "buy back shares",
                        "repurchase program", "stock repurchase"], 0.9),
    ("lawsuit", None, ["lawsuit", "sued", "litigation", "class action", "settlement",
                        "court ruling", "legal action", "judgment"], 0.85),
]


class EventClassifier:
    def predict(self, title: str, content: str) -> ClassificationResult:
        combined = (title + " " + content[:1000]).lower()
        best_label = "other"
        best_subtype = None
        best_score = 0.0

        scores: dict[str, float] = {}
        subtypes: dict[str, str | None] = {}

        for event_type, subtype, keywords, weight in _RULES:
            hit_count = sum(1 for kw in keywords if kw in combined)
            if hit_count == 0:
                continue
            # Score: weight * (hits / total_keywords), capped at weight
            score = weight * min(1.0, hit_count / max(1, len(keywords) * 0.3))
            if scores.get(event_type, 0) < score:
                scores[event_type] = score
                subtypes[event_type] = subtype

        if scores:
            best_label = max(scores, key=lambda k: scores[k])
            best_score = scores[best_label]
            best_subtype = subtypes[best_label]

        logger.debug("classifier.result", label=best_label, subtype=best_subtype, score=best_score)
        return ClassificationResult(
            label=best_label,
            subtype=best_subtype,
            confidence=round(best_score, 4),
        )
