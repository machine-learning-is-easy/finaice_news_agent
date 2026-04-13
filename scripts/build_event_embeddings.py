"""
Build / rebuild embeddings for all existing extracted_events that have no embedding yet.
Run from project root: python -m scripts.build_event_embeddings
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, text

from app.core.logging import setup_logging, get_logger
from app.db.session import AsyncSessionLocal
from app.db.models import ExtractedEventORM, EventEmbeddingORM
from app.retrieval.embedder import Embedder
from app.retrieval.vector_search import VectorSearch

setup_logging()
logger = get_logger("build_embeddings")


async def build_embeddings(batch_size: int = 50):
    embedder = Embedder()

    async with AsyncSessionLocal() as db:
        # Find events without an embedding
        result = await db.execute(
            select(ExtractedEventORM)
            .outerjoin(EventEmbeddingORM, ExtractedEventORM.id == EventEmbeddingORM.event_id)
            .where(EventEmbeddingORM.event_id.is_(None))
        )
        events = list(result.scalars().all())
        logger.info("build_embeddings.events_to_process", count=len(events))

        vector_search = VectorSearch(db)
        processed = 0

        for i in range(0, len(events), batch_size):
            batch = events[i:i + batch_size]
            texts = [
                f"{e.event_type} {e.event_subtype or ''}\n{e.fact_summary or ''}\n{e.impact_direction or ''}"
                for e in batch
            ]
            embeddings = embedder.embed_batch(texts)

            for event, embedding in zip(batch, embeddings):
                await vector_search.upsert_embedding(event.id, embedding)
                processed += 1

            await db.commit()
            logger.info("build_embeddings.batch_done", processed=processed, total=len(events))

    logger.info("build_embeddings.complete", total_processed=processed)


if __name__ == "__main__":
    asyncio.run(build_embeddings())
