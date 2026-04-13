from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AgentAnalysisORM
from app.agent.schemas import AgentAnalysis


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, event_id: int, analysis: AgentAnalysis, version: str = "v1") -> AgentAnalysisORM:
        orm = AgentAnalysisORM(
            event_id=event_id,
            analysis_version=version,
            final_label=analysis.final_label,
            final_score=analysis.final_score,
            time_horizon=analysis.time_horizon,
            causal_chain=analysis.causal_chain,
            risk_flags=analysis.risk_flags,
            reasoning_text=analysis.reasoning_text,
            user_readable_summary=analysis.user_readable_summary,
            machine_readable_output=analysis.machine_readable_output.model_dump(),
        )
        self.db.add(orm)
        await self.db.flush()
        return orm

    async def get_by_event_id(self, event_id: int) -> Optional[AgentAnalysisORM]:
        result = await self.db.execute(
            select(AgentAnalysisORM).where(AgentAnalysisORM.event_id == event_id)
        )
        return result.scalar_one_or_none()

    async def list_high_impact(self, threshold: float = 0.7, limit: int = 20) -> list[AgentAnalysisORM]:
        result = await self.db.execute(
            select(AgentAnalysisORM)
            .where(AgentAnalysisORM.final_score >= threshold)
            .order_by(desc(AgentAnalysisORM.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
