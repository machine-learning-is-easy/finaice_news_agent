from datetime import datetime
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    String, Text, Index, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


class NewsArticleORM(Base):
    __tablename__ = "news_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    source = Column(String(100), nullable=False)
    source_url = Column(Text)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    published_at = Column(DateTime(timezone=True), nullable=False)
    language = Column(String(20), default="en")
    raw_hash = Column(String(128), unique=True)
    inserted_at = Column(DateTime(timezone=True), server_default=func.now())

    entities = relationship("NewsEntityORM", back_populates="article", cascade="all, delete-orphan")
    events = relationship("ExtractedEventORM", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_news_articles_published_at", "published_at"),
        Index("ix_news_articles_source", "source"),
    )


class NewsEntityORM(Base):
    __tablename__ = "news_entities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(BigInteger, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False)
    entity_name = Column(String(255), nullable=False)
    entity_type = Column(String(50))
    ticker = Column(String(20))
    confidence = Column(Float)
    role = Column(String(50))

    article = relationship("NewsArticleORM", back_populates="entities")

    __table_args__ = (
        Index("ix_news_entities_article_id", "article_id"),
        Index("ix_news_entities_ticker", "ticker"),
    )


class ExtractedEventORM(Base):
    __tablename__ = "extracted_events"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    article_id = Column(BigInteger, ForeignKey("news_articles.id", ondelete="CASCADE"), nullable=False)
    primary_ticker = Column(String(20))
    event_type = Column(String(50), nullable=False)
    event_subtype = Column(String(100))
    sentiment_label = Column(String(20))
    sentiment_score = Column(Float)
    relevance_score = Column(Float)
    novelty_score = Column(Float)
    impact_direction = Column(String(20))
    impact_strength = Column(Float)
    time_horizon = Column(String(50))
    confidence = Column(Float)
    fact_summary = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    article = relationship("NewsArticleORM", back_populates="events")
    embedding = relationship("EventEmbeddingORM", back_populates="event", uselist=False, cascade="all, delete-orphan")
    analysis = relationship("AgentAnalysisORM", back_populates="event", uselist=False, cascade="all, delete-orphan")
    similar_from = relationship(
        "SimilarEventLinkORM",
        foreign_keys="SimilarEventLinkORM.event_id",
        back_populates="event",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_extracted_events_article_id", "article_id"),
        Index("ix_extracted_events_ticker", "primary_ticker"),
        Index("ix_extracted_events_event_type", "event_type"),
        Index("ix_extracted_events_created_at", "created_at"),
    )


class MarketSnapshotORM(Base):
    __tablename__ = "market_snapshots"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False)
    snapshot_time = Column(DateTime(timezone=True), nullable=False)
    price = Column(Float)
    volume = Column(BigInteger)
    day_return = Column(Float)
    week_return = Column(Float)
    volatility_20d = Column(Float)
    sector_etf = Column(String(20))
    sector_return = Column(Float)
    benchmark_return = Column(Float)
    earnings_date = Column(DateTime(timezone=True))
    market_regime = Column(String(50))

    __table_args__ = (
        Index("ix_market_snapshots_ticker_time", "ticker", "snapshot_time"),
    )


class EventEmbeddingORM(Base):
    __tablename__ = "event_embeddings"

    event_id = Column(BigInteger, ForeignKey("extracted_events.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(1536))

    event = relationship("ExtractedEventORM", back_populates="embedding")


class AgentAnalysisORM(Base):
    __tablename__ = "agent_analyses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False)
    analysis_version = Column(String(50), default="v1")
    final_label = Column(String(20))
    final_score = Column(Float)
    time_horizon = Column(String(50))
    causal_chain = Column(JSONB)
    risk_flags = Column(JSONB)
    reasoning_text = Column(Text)
    user_readable_summary = Column(Text)
    machine_readable_output = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("ExtractedEventORM", back_populates="analysis")

    __table_args__ = (
        Index("ix_agent_analyses_event_id", "event_id"),
        Index("ix_agent_analyses_final_label", "final_label"),
    )


class SimilarEventLinkORM(Base):
    __tablename__ = "similar_event_links"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(BigInteger, ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False)
    similar_event_id = Column(BigInteger, ForeignKey("extracted_events.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float)
    return_1d = Column(Float)
    return_5d = Column(Float)
    return_20d = Column(Float)

    event = relationship("ExtractedEventORM", foreign_keys=[event_id], back_populates="similar_from")

    __table_args__ = (
        Index("ix_similar_event_links_event_id", "event_id"),
    )
