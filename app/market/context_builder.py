from app.agent.schemas import MarketContext
from app.market.price_service import PriceService
from app.market.sector_service import SectorService
from app.core.logging import get_logger

logger = get_logger(__name__)


class MarketContextBuilder:
    def __init__(self):
        self.price_service = PriceService()
        self.sector_service = SectorService()

    def build(self, ticker: str) -> MarketContext:
        px = self.price_service.get_snapshot(ticker)
        sector = self.sector_service.get_sector_context(ticker)

        ctx = MarketContext(
            ticker=ticker,
            price=px["price"],
            day_return=px["day_return"],
            week_return=px["week_return"],
            volatility_20d=px["volatility_20d"],
            sector_etf=sector.get("sector_etf"),
            sector_return=sector.get("sector_return"),
            benchmark_return=sector.get("benchmark_return"),
            earnings_date=px.get("earnings_date"),
            market_regime=sector.get("market_regime"),
        )

        logger.info(
            "market_context.built",
            ticker=ticker,
            price=ctx.price,
            day_return=ctx.day_return,
            regime=ctx.market_regime,
        )
        return ctx
