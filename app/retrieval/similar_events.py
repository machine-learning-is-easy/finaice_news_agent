from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schemas import ExtractedEvent, SimilarEvent
from app.retrieval.embedder import Embedder
from app.retrieval.vector_search import VectorSearch
from app.core.logging import get_logger

logger = get_logger(__name__)


class SimilarEventRetriever:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.embedder = Embedder()
        self.vector_search = VectorSearch(db)

    async def retrieve(self, event: ExtractedEvent, top_k: int = 5) -> list[SimilarEvent]:
        text = f"{event.event_type} {event.event_subtype or ''}\n{event.fact_summary}\n{event.impact_direction}"
        embedding = self.embedder.embed_text(text)
        results = await self.vector_search.search_similar_events(
            embedding=embedding,
            top_k=top_k,
            exclude_event_id=event.article_id if event.article_id else None,
        )
        logger.info("similar_events.retrieved", count=len(results))
        return results

    async def store_embedding(self, event_id: int, event: ExtractedEvent) -> None:
        text = f"{event.event_type} {event.event_subtype or ''}\n{event.fact_summary}\n{event.impact_direction}"
        embedding = self.embedder.embed_text(text)
        await self.vector_search.upsert_embedding(event_id, embedding)
        logger.debug("similar_events.embedding_stored", event_id=event_id)
