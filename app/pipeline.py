"""
FinanceNewsAnalysisPipeline — the main orchestrator.
Ties together all modules in the correct order.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.schemas import NewsArticle, ExtractedEvent, AgentAnalysis, AnalyzeNewsResponse
from app.events.extractor import EventExtractor
from app.market.context_builder import MarketContextBuilder
from app.retrieval.similar_events import SimilarEventRetriever
from app.agent.reasoning_agent import ReasoningAgent
from app.agent.scoring_agent import ScoringAgent
from app.delivery.alert_engine import AlertEngine
from app.db.repositories.news_repository import NewsRepository
from app.db.repositories.event_repository import EventRepository
from app.db.repositories.analysis_repository import AnalysisRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class FinanceNewsAnalysisPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.event_extractor = EventExtractor()
        self.market_builder = MarketContextBuilder()
        self.scoring_agent = ScoringAgent()
        self.reasoning_agent = ReasoningAgent()
        self.alert_engine = AlertEngine()

        self.news_repo = NewsRepository(db)
        self.event_repo = EventRepository(db)
        self.analysis_repo = AnalysisRepository(db)

    async def run(self, article: NewsArticle) -> AnalyzeNewsResponse:
        # 1. Persist article (idempotent via hash)
        article_orm, is_new = await self.news_repo.get_or_create(article)
        article.id = article_orm.id

        if not is_new:
            logger.info("pipeline.duplicate_article_skipped", article_id=article_orm.id)

        # 2. Extract structured event
        event: ExtractedEvent = self.event_extractor.extract(article)
        event.article_id = article_orm.id

        # 3. Persist entities
        await self.news_repo.save_entities(article_orm.id, event.entities)

        # 4. Persist extracted event
        event_orm = await self.event_repo.create_event(event)
        event_id = event_orm.id

        # 5. Fetch market context
        market_context = None
        if event.primary_ticker:
            try:
                market_context = self.market_builder.build(event.primary_ticker)
                await self.event_repo.save_market_snapshot(market_context)
            except Exception as e:
                logger.warning("pipeline.market_context_failed", error=str(e))

        # 6. Quick score — decide whether to call full reasoning agent
        quick_score = self.scoring_agent.score(event, market_context)
        logger.info("pipeline.quick_score", score=quick_score, event_id=event_id)

        # 7. Retrieve similar historical events
        retriever = SimilarEventRetriever(self.db)
        similar_events = []
        if self.scoring_agent.should_run_full_analysis(quick_score):
            similar_events = await retriever.retrieve(event, top_k=5)
            await self.event_repo.save_similar_links(event_id, similar_events)

        # 8. Full reasoning agent
        analysis: AgentAnalysis = self.reasoning_agent.analyze(
            article=article,
            event=event,
            market_context=market_context,
            similar_events=similar_events,
        )

        # 9. Persist analysis
        analysis_orm = await self.analysis_repo.create(event_id, analysis)

        # 10. Store embedding for future retrieval
        await retriever.store_embedding(event_id, event)

        # 11. Fire alert if warranted
        if self.alert_engine.should_alert(event, analysis):
            self.alert_engine.fire_alert(event, analysis)

        logger.info(
            "pipeline.complete",
            article_id=article_orm.id,
            event_id=event_id,
            analysis_id=analysis_orm.id,
            label=analysis.final_label,
            score=analysis.final_score,
        )

        return AnalyzeNewsResponse(
            article_id=article_orm.id,
            event_id=event_id,
            analysis_id=analysis_orm.id,
            primary_ticker=event.primary_ticker,
            event_type=event.event_type,
            analysis=analysis,
        )
