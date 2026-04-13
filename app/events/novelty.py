"""
Novelty scorer.
Measures how surprising/unusual a piece of news is.
Phase 1: heuristic based on high-signal terms.
Phase 2: compare embedding against recent news pool.
"""
from dataclasses import dataclass
from app.core.logging import get_logger

logger = get_logger(__name__)

_HIGH_NOVELTY_SIGNALS = [
    "first time", "record", "unprecedented", "surprise", "unexpected",
    "shock", "shocked", "sudden", "abrupt", "emergency", "breaking",
    "major shift", "reversal", "historic", "all-time high", "all-time low",
    "largest ever", "biggest since", "first quarterly", "first annual",
]

_LOW_NOVELTY_SIGNALS = [
    "as expected", "in line with", "widely anticipated", "priced in",
    "consensus forecast", "already known", "previously announced",
]


def score_novelty(title: str, content: str) -> float:
    combined = (title + " " + content[:600]).lower()
    high_hits = sum(1 for s in _HIGH_NOVELTY_SIGNALS if s in combined)
    low_hits = sum(1 for s in _LOW_NOVELTY_SIGNALS if s in combined)

    base = 0.5
    score = base + high_hits * 0.08 - low_hits * 0.1
    result = round(max(0.1, min(1.0, score)), 4)
    logger.debug("novelty.score", score=result, high_hits=high_hits, low_hits=low_hits)
    return result
