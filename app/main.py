from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.api.routes_news import router as news_router
from app.api.routes_analysis import router as analysis_router
from app.api.routes_alerts import router as alerts_router

settings = get_settings()
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app.startup", env=settings.app_env, model=settings.reasoning_model)
    yield
    logger.info("app.shutdown")


app = FastAPI(
    title="Finance News Analysis Agent",
    description=(
        "Event-driven financial news analysis pipeline. "
        "Extracts structured events, enriches with market context, "
        "retrieves similar historical events, and produces causal-chain reasoning via Claude."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(news_router)
app.include_router(analysis_router)
app.include_router(alerts_router)


@app.get("/health", tags=["system"])
async def health_check() -> dict:
    return {"status": "ok", "version": "0.1.0", "model": settings.reasoning_model}
