import hashlib
from datetime import datetime
from typing import Optional
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import NewsArticleORM, NewsEntityORM
from app.agent.schemas import NewsArticle, EntityMention


def _hash_article(title: str, content: str) -> str:
    raw = f"{title}||{content}"
    return hashlib.sha256(raw.encode()).hexdigest()


class NewsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_hash(self, raw_hash: str) -> Optional[NewsArticleORM]:
        result = await self.db.execute(
            select(NewsArticleORM).where(NewsArticleORM.raw_hash == raw_hash)
        )
        return result.scalar_one_or_none()

    async def create(self, article: NewsArticle) -> NewsArticleORM:
        raw_hash = _hash_article(article.title, article.content)
        orm = NewsArticleORM(
            source=article.source,
            source_url=article.source_url,
            title=article.title,
            content=article.content,
            published_at=article.published_at,
            language=article.language,
            raw_hash=raw_hash,
        )
        self.db.add(orm)
        await self.db.flush()
        return orm

    async def get_or_create(self, article: NewsArticle) -> tuple[NewsArticleORM, bool]:
        raw_hash = _hash_article(article.title, article.content)
        existing = await self.find_by_hash(raw_hash)
        if existing:
            return existing, False
        new_article = await self.create(article)
        return new_article, True

    async def save_entities(self, article_id: int, entities: list[EntityMention]) -> None:
        for ent in entities:
            orm = NewsEntityORM(
                article_id=article_id,
                entity_name=ent.entity_name,
                entity_type=ent.entity_type,
                ticker=ent.ticker,
                confidence=ent.confidence,
                role=ent.role,
            )
            self.db.add(orm)
        await self.db.flush()

    async def list_recent(self, limit: int = 50) -> list[NewsArticleORM]:
        result = await self.db.execute(
            select(NewsArticleORM)
            .order_by(desc(NewsArticleORM.published_at))
            .limit(limit)
        )
        return list(result.scalars().all())
