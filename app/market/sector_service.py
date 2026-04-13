"""
Provides sector and benchmark context for a given ticker.
"""
import yfinance as yf
from app.entity.aliases import TICKER_SECTOR, SECTOR_ETFS
from app.core.logging import get_logger

logger = get_logger(__name__)

_BENCHMARK = "SPY"


class SectorService:
    def get_sector_context(self, ticker: str) -> dict:
        sector = TICKER_SECTOR.get(ticker.upper())
        sector_etf = SECTOR_ETFS.get(sector, None) if sector else None
        benchmark_return = self._get_1d_return(_BENCHMARK)
        sector_return = self._get_1d_return(sector_etf) if sector_etf else None
        market_regime = self._classify_regime(benchmark_return)

        return {
            "sector": sector,
            "sector_etf": sector_etf,
            "sector_return": sector_return,
            "benchmark_return": benchmark_return,
            "market_regime": market_regime,
        }

    def _get_1d_return(self, ticker: str | None) -> float | None:
        if not ticker:
            return None
        try:
            hist = yf.Ticker(ticker).history(period="5d", interval="1d")
            if len(hist) < 2:
                return None
            latest = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            return round((latest - prev) / prev, 6) if prev else None
        except Exception as e:
            logger.warning("sector_service.return_error", ticker=ticker, error=str(e))
            return None

    def _classify_regime(self, benchmark_return: float | None) -> str:
        if benchmark_return is None:
            return "unknown"
        if benchmark_return > 0.01:
            return "risk_on"
        if benchmark_return < -0.01:
            return "risk_off"
        return "neutral"
