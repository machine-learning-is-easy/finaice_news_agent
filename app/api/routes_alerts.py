from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.db.repositories.event_repository import EventRepository
from app.db.repositories.analysis_repository import AnalysisRepository
from app.core.config import get_settings

router = APIRouter(prefix="/alerts", tags=["alerts"])
settings = get_settings()


@router.get("/high-impact", summary="Get recent high-impact alerts")
async def get_high_impact_alerts(
    threshold: float = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """
    Returns recent events whose analysis final_score is above the threshold.
    Defaults to the configured alert threshold.
    """
    threshold = threshold or settings.alert_impact_threshold
    repo = AnalysisRepository(db)
    analyses = await repo.list_high_impact(threshold=threshold, limit=limit)

    alerts = []
    for a in analyses:
        alerts.append({
            "analysis_id": a.id,
            "event_id": a.event_id,
            "final_label": a.final_label,
            "final_score": a.final_score,
            "time_horizon": a.time_horizon,
            "user_readable_summary": a.user_readable_summary,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    return alerts
