"""
pgvector-based similarity search for events.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schemas import SimilarEvent
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorSearch:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search_similar_events(
        self,
        embedding: list[float],
        top_k: int = 5,
        exclude_event_id: int | None = None,
    ) -> list[SimilarEvent]:
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"

        sql = text("""
            SELECT
                ee.event_id,
                e.event_type,
                e.primary_ticker,
                e.fact_summary,
                1 - (ee.embedding <=> :embedding::vector) AS similarity_score,
                sel.return_1d,
                sel.return_5d,
                sel.return_20d
            FROM event_embeddings ee
            JOIN extracted_events e ON e.id = ee.event_id
            LEFT JOIN similar_event_links sel ON sel.similar_event_id = ee.event_id
            WHERE (:exclude_id IS NULL OR ee.event_id != :exclude_id)
            ORDER BY ee.embedding <=> :embedding::vector
            LIMIT :top_k
        """)

        try:
            result = await self.db.execute(
                sql,
                {"embedding": vec_str, "top_k": top_k, "exclude_id": exclude_event_id},
            )
            rows = result.fetchall()

            similar = []
            for row in rows:
                similar.append(SimilarEvent(
                    event_id=row.event_id,
                    event_type=row.event_type,
                    primary_ticker=row.primary_ticker,
                    similarity_score=round(float(row.similarity_score), 4),
                    fact_summary=row.fact_summary or "",
                    return_1d=row.return_1d,
                    return_5d=row.return_5d,
                    return_20d=row.return_20d,
                ))
            return similar

        except Exception as e:
            logger.warning("vector_search.error", error=str(e))
            return []

    async def upsert_embedding(self, event_id: int, embedding: list[float]) -> None:
        vec_str = "[" + ",".join(str(v) for v in embedding) + "]"
        sql = text("""
            INSERT INTO event_embeddings (event_id, embedding)
            VALUES (:event_id, :embedding::vector)
            ON CONFLICT (event_id) DO UPDATE SET embedding = EXCLUDED.embedding
        """)
        await self.db.execute(sql, {"event_id": event_id, "embedding": vec_str})
