"""
Lightweight scoring agent.
Produces a quick impact score without a full LLM call.
Used for fast pre-filtering before the full reasoning agent runs.
"""
from app.agent.schemas import ExtractedEvent, MarketContext
from app.core.logging import get_logger

logger = get_logger(__name__)

_HIGH_IMPACT_EVENTS = {"earnings", "guidance", "merger", "regulation", "macro_data"}
_VOLATILE_REGIME = {"high_vol", "risk_off"}


class ScoringAgent:
    """
    Heuristic scoring: combine event signal strength with market context.
    Returns a score in [0, 1].
    """

    def score(self, event: ExtractedEvent, market_context: MarketContext | None) -> float:
        base = event.impact_strength

        # Boost for high-impact event types
        if event.event_type in _HIGH_IMPACT_EVENTS:
            base = min(1.0, base + 0.1)

        # Boost for high novelty
        if event.novelty_score > 0.7:
            base = min(1.0, base + 0.05)

        # Adjust for market regime
        if market_context:
            if market_context.market_regime in _VOLATILE_REGIME:
                base = min(1.0, base + 0.08)
            # Discount if volatility is very low (suggests priced in)
            if market_context.volatility_20d < 0.10:
                base = max(0.0, base - 0.05)

        return round(base, 4)

    def should_run_full_analysis(self, score: float, threshold: float = 0.35) -> bool:
        return score >= threshold
