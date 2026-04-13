from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NewsArticle(BaseModel):
    id: Optional[int] = None
    source: str
    title: str
    content: str
    source_url: Optional[str] = None
    published_at: datetime
    language: str = "en"
    raw_hash: Optional[str] = None


class EntityMention(BaseModel):
    entity_name: str
    entity_type: str  # company, person, index, commodity
    ticker: Optional[str] = None
    confidence: float = 0.0
    role: Optional[str] = None  # primary_subject, secondary_subject, mentioned


class ExtractedEvent(BaseModel):
    article_id: int
    primary_ticker: Optional[str] = None
    event_type: str
    event_subtype: Optional[str] = None
    sentiment_label: str  # positive, negative, neutral
    sentiment_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    impact_direction: str  # positive, negative, neutral
    impact_strength: float = Field(ge=0.0, le=1.0)
    time_horizon: str  # intraday, 1d-3d, 1w-1m, long_term
    confidence: float = Field(ge=0.0, le=1.0)
    fact_summary: str
    entities: list[EntityMention] = []


class MarketContext(BaseModel):
    ticker: str
    price: float
    day_return: float
    week_return: float
    volatility_20d: float
    sector_etf: Optional[str] = None
    sector_return: Optional[float] = None
    benchmark_return: Optional[float] = None  # SPY return same period
    earnings_date: Optional[str] = None
    market_regime: Optional[str] = None  # risk_on, risk_off, high_vol


class SimilarEvent(BaseModel):
    event_id: int
    event_type: str
    primary_ticker: Optional[str] = None
    similarity_score: float
    fact_summary: str
    return_1d: Optional[float] = None
    return_5d: Optional[float] = None
    return_20d: Optional[float] = None


class MachineReadableOutput(BaseModel):
    affected_tickers: list[str] = []
    sector_impact: str = ""
    macro_relevance: float = 0.0
    event_novelty: float = 0.0
    price_in_probability: float = 0.0


class AgentAnalysis(BaseModel):
    final_label: str  # positive, negative, neutral
    final_score: float = Field(ge=0.0, le=1.0)
    causal_chain: list[str] = []
    risk_flags: list[str] = []
    time_horizon: str = "1d-3d"
    reasoning_text: str
    user_readable_summary: str
    machine_readable_output: MachineReadableOutput = Field(default_factory=MachineReadableOutput)


# --- API request/response models ---

class AnalyzeNewsRequest(BaseModel):
    source: str
    title: str
    content: str
    source_url: Optional[str] = None
    published_at: datetime


class AnalyzeNewsResponse(BaseModel):
    article_id: Optional[int] = None
    event_id: Optional[int] = None
    analysis_id: Optional[int] = None
    primary_ticker: Optional[str] = None
    event_type: str
    analysis: AgentAnalysis


class TickerEventsResponse(BaseModel):
    ticker: str
    events: list[dict]


class AlertItem(BaseModel):
    event_id: int
    article_id: int
    ticker: Optional[str]
    event_type: str
    impact_direction: str
    impact_strength: float
    final_label: str
    final_score: float
    user_readable_summary: str
    published_at: datetime
