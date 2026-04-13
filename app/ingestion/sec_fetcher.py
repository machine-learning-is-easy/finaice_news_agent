"""
SEC EDGAR filing fetcher.
Retrieves recent 8-K and 10-Q/10-K filings for a given ticker.
"""
import httpx
from datetime import datetime, timezone

from app.agent.schemas import NewsArticle
from app.ingestion.cleaner import clean_article_text, truncate
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

_EDGAR_BASE = "https://data.sec.gov"
_HEADERS = {"User-Agent": settings.sec_user_agent}

# Filing types to ingest
_RELEVANT_FORMS = {"8-K", "10-Q", "10-K"}


class SECFetcher:
    def fetch_recent_filings(self, ticker: str, limit: int = 10) -> list[NewsArticle]:
        """
        Fetch recent SEC filings for a ticker symbol.
        Returns them as NewsArticle objects for pipeline compatibility.
        """
        cik = self._resolve_cik(ticker)
        if not cik:
            logger.warning("sec_fetcher.cik_not_found", ticker=ticker)
            return []

        return self._get_filings(cik, ticker, limit)

    def _resolve_cik(self, ticker: str) -> str | None:
        url = f"{_EDGAR_BASE}/submissions/CIK{ticker.upper().zfill(10)}.json"
        # EDGAR lookup by ticker name via company_tickers.json
        try:
            resp = httpx.get(
                "https://www.sec.gov/files/company_tickers.json",
                headers=_HEADERS,
                timeout=10,
            )
            data = resp.json()
            for entry in data.values():
                if entry.get("ticker", "").upper() == ticker.upper():
                    return str(entry["cik_str"]).zfill(10)
        except Exception as e:
            logger.error("sec_fetcher.cik_resolution_error", ticker=ticker, error=str(e))
        return None

    def _get_filings(self, cik: str, ticker: str, limit: int) -> list[NewsArticle]:
        url = f"{_EDGAR_BASE}/submissions/CIK{cik}.json"
        try:
            resp = httpx.get(url, headers=_HEADERS, timeout=10)
            data = resp.json()
            filings = data.get("filings", {}).get("recent", {})

            forms = filings.get("form", [])
            dates = filings.get("filingDate", [])
            accs = filings.get("accessionNumber", [])
            descriptions = filings.get("primaryDocument", [])

            articles = []
            for form, date_str, acc, doc in zip(forms, dates, accs, descriptions):
                if form not in _RELEVANT_FORMS:
                    continue
                acc_clean = acc.replace("-", "")
                filing_url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_clean}/{doc}"
                articles.append(NewsArticle(
                    source="SEC EDGAR",
                    title=f"{ticker} {form} Filing — {date_str}",
                    content=f"SEC {form} filing by {ticker}. See full document at: {filing_url}",
                    source_url=filing_url,
                    published_at=datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc),
                    language="en",
                ))
                if len(articles) >= limit:
                    break

            logger.info("sec_fetcher.done", ticker=ticker, count=len(articles))
            return articles

        except Exception as e:
            logger.error("sec_fetcher.error", cik=cik, error=str(e))
            return []
