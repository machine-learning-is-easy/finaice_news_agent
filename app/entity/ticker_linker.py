import re
from app.agent.schemas import EntityMention
from app.entity.aliases import COMPANY_ALIASES
from app.core.logging import get_logger

logger = get_logger(__name__)

# Pattern to detect raw ticker symbols like $AAPL or (NASDAQ: NVDA)
TICKER_PATTERN = re.compile(
    r"(?:\$([A-Z]{1,5})|"
    r"(?:NYSE|NASDAQ|AMEX):\s*([A-Z]{1,5}))",
    re.IGNORECASE,
)


class TickerLinker:
    """
    Maps entity mentions in text to stock tickers.
    Strategy:
      1. Regex scan for explicit ticker symbols ($AAPL, NYSE: NVDA)
      2. Fuzzy alias lookup against the static alias table
    """

    def link(self, text: str) -> list[EntityMention]:
        mentions: list[EntityMention] = []
        seen_tickers: set[str] = set()

        # Pass 1: explicit ticker patterns
        for match in TICKER_PATTERN.finditer(text):
            ticker = (match.group(1) or match.group(2)).upper()
            if ticker not in seen_tickers:
                seen_tickers.add(ticker)
                mentions.append(EntityMention(
                    entity_name=ticker,
                    entity_type="company",
                    ticker=ticker,
                    confidence=0.95,
                    role="primary_subject" if not mentions else "secondary_subject",
                ))

        # Pass 2: alias dictionary lookup (case-insensitive substring match)
        text_lower = text.lower()
        for alias, ticker in COMPANY_ALIASES.items():
            if alias in text_lower and ticker not in seen_tickers:
                seen_tickers.add(ticker)
                # Estimate confidence by how specific the alias is
                confidence = min(0.9, 0.5 + len(alias) * 0.02)
                mentions.append(EntityMention(
                    entity_name=alias.title(),
                    entity_type="company",
                    ticker=ticker,
                    confidence=round(confidence, 3),
                    role="primary_subject" if not mentions else "mentioned",
                ))

        # Sort: highest confidence first, promote first one to primary_subject
        mentions.sort(key=lambda m: -m.confidence)
        for i, m in enumerate(mentions):
            m.role = "primary_subject" if i == 0 else ("secondary_subject" if i == 1 else "mentioned")

        logger.debug("ticker_linker.result", count=len(mentions), tickers=[m.ticker for m in mentions])
        return mentions
