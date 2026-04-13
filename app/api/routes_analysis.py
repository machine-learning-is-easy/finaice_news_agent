from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.event_repository import EventRepository
from app.db.repositories.analysis_repository import AnalysisRepository
from app.agent.formatter import AnalysisFormatter
from app.core.logging import get_logger

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = get_logger(__name__)
formatter = AnalysisFormatter()


@router.get("/ticker/{ticker}/events", summary="Get recent events for a ticker")
async def get_ticker_events(
    ticker: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    repo = EventRepository(db)
    events = await repo.get_events_by_ticker(ticker.upper(), limit=limit)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "event_subtype": e.event_subtype,
            "sentiment_label": e.sentiment_label,
            "impact_direction": e.impact_direction,
            "impact_strength": e.impact_strength,
            "novelty_score": e.novelty_score,
            "fact_summary": e.fact_summary,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/event/{event_id}", summary="Get full analysis for an event")
async def get_event_analysis(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    repo = AnalysisRepository(db)
    analysis_orm = await repo.get_by_event_id(event_id)
    if not analysis_orm:
        raise HTTPException(status_code=404, detail="Analysis not found for this event_id")
    return {
        "event_id": analysis_orm.event_id,
        "final_label": analysis_orm.final_label,
        "final_score": analysis_orm.final_score,
        "time_horizon": analysis_orm.time_horizon,
        "causal_chain": analysis_orm.causal_chain,
        "risk_flags": analysis_orm.risk_flags,
        "user_readable_summary": analysis_orm.user_readable_summary,
        "reasoning_text": analysis_orm.reasoning_text,
        "machine_readable_output": analysis_orm.machine_readable_output,
        "created_at": analysis_orm.created_at.isoformat() if analysis_orm.created_at else None,
    }


@router.get("/event/{event_id}/report", summary="Get markdown report for an event")
async def get_event_report(
    event_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.db.models import ExtractedEventORM, AgentAnalysisORM
    from app.agent.schemas import AgentAnalysis, ExtractedEvent, MachineReadableOutput
    from sqlalchemy import select

    result = await db.execute(
        select(ExtractedEventORM).where(ExtractedEventORM.id == event_id)
    )
    event_orm = result.scalar_one_or_none()
    if not event_orm:
        raise HTTPException(status_code=404, detail="Event not found")

    analysis_repo = AnalysisRepository(db)
    analysis_orm = await analysis_repo.get_by_event_id(event_id)
    if not analysis_orm:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Reconstruct Pydantic objects for formatting
    event = ExtractedEvent(
        article_id=event_orm.article_id,
        primary_ticker=event_orm.primary_ticker,
        event_type=event_orm.event_type,
        event_subtype=event_orm.event_subtype,
        sentiment_label=event_orm.sentiment_label or "neutral",
        sentiment_score=event_orm.sentiment_score or 0.5,
        relevance_score=event_orm.relevance_score or 0.5,
        novelty_score=event_orm.novelty_score or 0.5,
        impact_direction=event_orm.impact_direction or "neutral",
        impact_strength=event_orm.impact_strength or 0.5,
        time_horizon=event_orm.time_horizon or "1d-3d",
        confidence=event_orm.confidence or 0.5,
        fact_summary=event_orm.fact_summary or "",
    )
    machine = analysis_orm.machine_readable_output or {}
    analysis = AgentAnalysis(
        final_label=analysis_orm.final_label or "neutral",
        final_score=analysis_orm.final_score or 0.5,
        causal_chain=analysis_orm.causal_chain or [],
        risk_flags=analysis_orm.risk_flags or [],
        time_horizon=analysis_orm.time_horizon or "1d-3d",
        reasoning_text=analysis_orm.reasoning_text or "",
        user_readable_summary=analysis_orm.user_readable_summary or "",
        machine_readable_output=MachineReadableOutput(**machine),
    )

    report = formatter.to_markdown_report(analysis, event)
    return {"report": report}
