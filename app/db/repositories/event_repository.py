from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ExtractedEventORM, MarketSnapshotORM, SimilarEventLinkORM
from app.agent.schemas import ExtractedEvent, MarketContext, SimilarEvent


class EventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_event(self, event: ExtractedEvent) -> ExtractedEventORM:
        orm = ExtractedEventORM(
            article_id=event.article_id,
            primary_ticker=event.primary_ticker,
            event_type=event.event_type,
            event_subtype=event.event_subtype,
            sentiment_label=event.sentiment_label,
            sentiment_score=event.sentiment_score,
            relevance_score=event.relevance_score,
            novelty_score=event.novelty_score,
            impact_direction=event.impact_direction,
            impact_strength=event.impact_strength,
            time_horizon=event.time_horizon,
            confidence=event.confidence,
            fact_summary=event.fact_summary,
        )
        self.db.add(orm)
        await self.db.flush()
        return orm

    async def save_market_snapshot(self, ctx: MarketContext) -> MarketSnapshotORM:
        from datetime import datetime, timezone
        orm = MarketSnapshotORM(
            ticker=ctx.ticker,
            snapshot_time=datetime.now(timezone.utc),
            price=ctx.price,
            day_return=ctx.day_return,
            week_return=ctx.week_return,
            volatility_20d=ctx.volatility_20d,
            sector_etf=ctx.sector_etf,
            sector_return=ctx.sector_return,
            benchmark_return=ctx.benchmark_return,
            market_regime=ctx.market_regime,
        )
        self.db.add(orm)
        await self.db.flush()
        return orm

    async def save_similar_links(self, event_id: int, similar_events: list[SimilarEvent]) -> None:
        for sim in similar_events:
            link = SimilarEventLinkORM(
                event_id=event_id,
                similar_event_id=sim.event_id,
                similarity_score=sim.similarity_score,
                return_1d=sim.return_1d,
                return_5d=sim.return_5d,
                return_20d=sim.return_20d,
            )
            self.db.add(link)
        await self.db.flush()

    async def get_events_by_ticker(self, ticker: str, limit: int = 20) -> list[ExtractedEventORM]:
        result = await self.db.execute(
            select(ExtractedEventORM)
            .where(ExtractedEventORM.primary_ticker == ticker)
            .order_by(desc(ExtractedEventORM.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_high_impact_events(self, threshold: float = 0.7, limit: int = 50) -> list[ExtractedEventORM]:
        result = await self.db.execute(
            select(ExtractedEventORM)
            .where(ExtractedEventORM.impact_strength >= threshold)
            .order_by(desc(ExtractedEventORM.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
