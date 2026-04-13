"""
Fetches real-time and historical price data via yfinance.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

import yfinance as yf

from app.core.logging import get_logger

logger = get_logger(__name__)


class PriceService:
    def get_snapshot(self, ticker: str) -> dict:
        """
        Returns a price snapshot dict for the given ticker.
        Falls back to empty values if the ticker is invalid or data unavailable.
        """
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo", interval="1d")
            if hist.empty:
                return self._empty_snapshot(ticker)

            latest_price = float(hist["Close"].iloc[-1])
            prev_day_price = float(hist["Close"].iloc[-2]) if len(hist) > 1 else latest_price
            week_ago_price = float(hist["Close"].iloc[-6]) if len(hist) > 5 else latest_price

            day_return = (latest_price - prev_day_price) / prev_day_price if prev_day_price else 0.0
            week_return = (latest_price - week_ago_price) / week_ago_price if week_ago_price else 0.0
            volatility_20d = float(hist["Close"].pct_change().std() * (252 ** 0.5)) if len(hist) >= 20 else 0.0

            # Earnings date
            try:
                cal = stock.calendar
                earnings_date = None
                if cal is not None and not cal.empty:
                    earnings_date = str(cal.iloc[0, 0].date()) if len(cal) > 0 else None
            except Exception:
                earnings_date = None

            snapshot = {
                "ticker": ticker,
                "price": round(latest_price, 2),
                "day_return": round(day_return, 6),
                "week_return": round(week_return, 6),
                "volatility_20d": round(volatility_20d, 6),
                "earnings_date": earnings_date,
            }
            logger.debug("price_service.snapshot", **{k: v for k, v in snapshot.items() if k != "ticker"})
            return snapshot

        except Exception as e:
            logger.warning("price_service.error", ticker=ticker, error=str(e))
            return self._empty_snapshot(ticker)

    def _empty_snapshot(self, ticker: str) -> dict:
        return {
            "ticker": ticker,
            "price": 0.0,
            "day_return": 0.0,
            "week_return": 0.0,
            "volatility_20d": 0.0,
            "earnings_date": None,
        }
