from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schemas import AnalyzeNewsRequest, AnalyzeNewsResponse, NewsArticle
from app.db.session import get_db
from app.db.repositories.news_repository import NewsRepository
from app.pipeline import FinanceNewsAnalysisPipeline
from app.core.logging import get_logger

router = APIRouter(prefix="/news", tags=["news"])
logger = get_logger(__name__)


@router.post("/analyze", response_model=AnalyzeNewsResponse, summary="Analyze a news article")
async def analyze_news(
    request: AnalyzeNewsRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeNewsResponse:
    """
    Submit a news article and receive a full financial event analysis.
    Runs the complete pipeline: event extraction → market context → RAG → LLM reasoning.
    """
    article = NewsArticle(
        source=request.source,
        title=request.title,
        content=request.content,
        source_url=request.source_url,
        published_at=request.published_at,
    )

    pipeline = FinanceNewsAnalysisPipeline(db)
    try:
        result = await pipeline.run(article)
    except Exception as e:
        logger.error("routes_news.analyze_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Pipeline error: {e}")

    return result


@router.get("/recent", summary="List recently ingested articles")
async def list_recent_news(
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    repo = NewsRepository(db)
    articles = await repo.list_recent(limit=limit)
    return [
        {
            "id": a.id,
            "source": a.source,
            "title": a.title,
            "published_at": a.published_at.isoformat(),
            "source_url": a.source_url,
        }
        for a in articles
    ]
