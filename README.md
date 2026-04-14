# Finance News Analysis Agent

An event-driven financial news analysis pipeline powered by Claude (Anthropic). Ingests news from RSS feeds and SEC EDGAR, extracts structured events, enriches them with live market context, retrieves similar historical events via vector search, and produces causal-chain reasoning with dual human/machine-readable output.

---

## Table of Contents

- [Architecture](#architecture)
- [Repository Structure](#repository-structure)
- [Pipeline Workflow](#pipeline-workflow)
- [API Reference](#api-reference)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Server](#running-the-server)
- [Scripts](#scripts)
- [Testing](#testing)
- [Debugging Guide](#debugging-guide)
- [Development Roadmap](#development-roadmap)

---

## Architecture

```
               ┌────────────────────┐
               │   News Sources      │
               │ RSS / SEC EDGAR     │
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Ingestion Layer    │
               │  fetch / clean /    │
               │  deduplicate        │
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Entity Linking     │
               │  ticker mapping /   │
               │  NER extraction     │
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Event Extraction   │
               │  classify / score   │
               │  sentiment / novelty│
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Market Context     │
               │  price / vol /      │
               │  sector / regime    │
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Similar Event RAG  │
               │  pgvector cosine    │
               │  similarity search  │
               └─────────┬──────────┘
                         │
                         ▼
               ┌────────────────────┐
               │  Reasoning Agent    │
               │  Claude API /       │
               │  causal-chain +     │
               │  impact scoring     │
               └─────────┬──────────┘
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  REST API    │ │ Alert Engine │ │Content Engine│
│  /analyze   │ │ threshold    │ │ LinkedIn /   │
│  /events    │ │ triggers     │ │ video script │
└──────────────┘ └──────────────┘ └──────────────┘
```

**Stack:**

| Layer | Technology |
|---|---|
| API | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + pgvector |
| Cache | Redis 7 |
| ORM / Migrations | SQLAlchemy 2 async + Alembic |
| LLM Reasoning | Claude (`claude-sonnet-4-6`) via Anthropic API |
| Embeddings | OpenAI `text-embedding-3-small` (1536-dim) |
| Finance data | yfinance |
| NLP | spaCy `en_core_web_sm` |
| Async tasks | Celery + Kombu (Phase 2) |
| Containerisation | Docker + Docker Compose |

---

## Repository Structure

```
finaice_news_agent/
│
├── main.py                        # Entry point — runs uvicorn
├── requirements.txt
├── Dockerfile
├── docker-compose.yml             # Postgres + Redis + API
├── alembic.ini
├── .env.example                   # Copy to .env and fill in keys
│
├── alembic/
│   ├── env.py                     # Async Alembic config
│   └── versions/                  # Auto-generated migration files
│
├── app/
│   ├── main.py                    # FastAPI app, router registration
│   │
│   ├── pipeline.py                # FinanceNewsAnalysisPipeline — main orchestrator
│   │
│   ├── core/
│   │   ├── config.py              # Pydantic-settings (reads .env)
│   │   ├── logging.py             # structlog setup
│   │   └── prompts.py             # All LLM prompt templates
│   │
│   ├── db/
│   │   ├── models.py              # SQLAlchemy ORM models (7 tables)
│   │   ├── session.py             # Async + sync engine / session factories
│   │   └── repositories/
│   │       ├── news_repository.py      # CRUD for news_articles + entities
│   │       ├── event_repository.py     # CRUD for extracted_events, snapshots
│   │       └── analysis_repository.py  # CRUD for agent_analyses
│   │
│   ├── ingestion/
│   │   ├── rss_fetcher.py         # RSS/Atom feed parser → NewsArticle
│   │   ├── sec_fetcher.py         # SEC EDGAR 8-K / 10-Q / 10-K fetcher
│   │   └── cleaner.py             # HTML stripping, whitespace normalisation
│   │
│   ├── entity/
│   │   ├── aliases.py             # Static company → ticker map (58 entries)
│   │   ├── ticker_linker.py       # Regex ($AAPL) + alias lookup → EntityMention
│   │   └── ner.py                 # spaCy ORG/PERSON extractor (optional)
│   │
│   ├── events/
│   │   ├── classifier.py          # Keyword-rule event type classifier (11 types)
│   │   ├── sentiment.py           # Financial sentiment (positive/negative/neutral)
│   │   ├── novelty.py             # Novelty scorer (high-signal keyword heuristic)
│   │   └── extractor.py           # EventExtractor — combines all three above
│   │
│   ├── market/
│   │   ├── price_service.py       # yfinance price / vol / earnings date snapshot
│   │   ├── sector_service.py      # Sector ETF return + market regime classifier
│   │   └── context_builder.py     # Builds MarketContext from price + sector data
│   │
│   ├── retrieval/
│   │   ├── embedder.py            # OpenAI / local embedding wrapper
│   │   ├── vector_search.py       # pgvector cosine similarity queries
│   │   └── similar_events.py      # SimilarEventRetriever — embed + search + store
│   │
│   ├── agent/
│   │   ├── schemas.py             # All Pydantic models (NewsArticle, ExtractedEvent,
│   │   │                          #   MarketContext, SimilarEvent, AgentAnalysis, …)
│   │   ├── reasoning_agent.py     # Claude API call with prompt caching
│   │   ├── scoring_agent.py       # Heuristic quick-score (no LLM cost)
│   │   └── formatter.py           # Markdown report + short alert formatter
│   │
│   ├── api/
│   │   ├── routes_news.py         # POST /news/analyze, GET /news/recent
│   │   ├── routes_analysis.py     # GET /analysis/ticker/{t}/events,
│   │   │                          #   GET /analysis/event/{id}[/report]
│   │   └── routes_alerts.py       # GET /alerts/high-impact
│   │
│   └── delivery/
│       ├── alert_engine.py        # Threshold-based alert firing
│       ├── report_generator.py    # Markdown / daily digest generator
│       └── social_writer.py       # LinkedIn post + video script via Claude
│
├── scripts/
│   ├── backfill_news.py           # Fetch RSS feeds and run pipeline on all articles
│   ├── build_event_embeddings.py  # Backfill pgvector embeddings for existing events
│   └── verify_env.py              # Checks all 30 dependencies are importable
│
└── tests/
    └── test_pipeline_unit.py      # 16 unit tests (no DB / no LLM required)
```

### Database schema (7 tables)

```
news_articles          — raw ingested articles (deduplicated by SHA-256 hash)
news_entities          — entity/ticker mentions per article
extracted_events       — structured event per article (type, sentiment, impact)
market_snapshots       — price/vol/sector context at time of event
event_embeddings       — 1536-dim pgvector embedding per event
agent_analyses         — Claude's causal-chain reasoning output (JSONB)
similar_event_links    — top-K similar historical events with forward returns
```

---

## Pipeline Workflow

A single call to `FinanceNewsAnalysisPipeline.run(article)` executes these steps in order:

```
Step 1  — Deduplication
          SHA-256 hash of title+content → skip if already in DB

Step 2  — Event Extraction
          ticker_linker  : regex ($AAPL) + alias table → primary ticker
          classifier     : keyword rules → event_type (earnings/merger/…)
          sentiment      : keyword scoring → positive/negative/neutral
          novelty        : signal word scoring → 0–1 surprise score

Step 3  — Persist entities + extracted_event to DB

Step 4  — Market Context (if ticker found)
          yfinance       : price, day_return, week_return, volatility_20d
          sector_service : sector ETF return, SPY benchmark, market_regime

Step 5  — Quick Score (ScoringAgent, no LLM)
          Heuristic: impact_strength + event_type boost + novelty boost
          If score < 0.35  →  skip full LLM call (save API cost)

Step 6  — Similar Event Retrieval (RAG)
          Embed event text → pgvector cosine search → top-5 similar events
          with their historical 1d / 5d / 20d forward returns

Step 7  — Reasoning Agent (Claude)
          Builds prompt from article + event + market_context + similar_events
          Returns: final_label, causal_chain, risk_flags, user_readable_summary

Step 8  — Persist analysis + store embedding

Step 9  — Alert Engine
          If final_score ≥ ALERT_IMPACT_THRESHOLD (default 0.7)
          or novelty_score ≥ ALERT_NOVELTY_THRESHOLD (default 0.6) → fire alert
```

### Data flow types

```
NewsArticle
    │ EventExtractor.extract()
    ▼
ExtractedEvent  ──→  MarketContext (MarketContextBuilder)
    │                     │
    │  SimilarEventRetriever.retrieve()
    ▼
[SimilarEvent, ...]
    │
    │  ReasoningAgent.analyze(article, event, market_context, similar_events)
    ▼
AgentAnalysis
    └─→ AnalyzeNewsResponse  (returned by API)
```

---

## API Reference

Base URL: `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs`

### POST `/news/analyze`

Submit a news article for full pipeline analysis.

**Request body:**
```json
{
  "source": "Reuters",
  "title": "Nvidia beats Q3 earnings, raises full-year guidance",
  "content": "Nvidia ($NVDA) reported Q3 EPS of $0.81...",
  "source_url": "https://reuters.com/...",
  "published_at": "2026-04-13T09:30:00Z"
}
```

**Response:**
```json
{
  "article_id": 1,
  "event_id": 1,
  "analysis_id": 1,
  "primary_ticker": "NVDA",
  "event_type": "earnings",
  "analysis": {
    "final_label": "positive",
    "final_score": 0.87,
    "causal_chain": [
      "EPS beat drives upward revision in analyst estimates",
      "Raised guidance signals sustained AI chip demand",
      "Positive guidance revisions typically expand P/E multiples in semiconductor sector"
    ],
    "risk_flags": [
      "Elevated valuation may limit upside despite beat",
      "Export control uncertainty could weigh on forward guidance credibility"
    ],
    "time_horizon": "1d-3d",
    "user_readable_summary": "Nvidia's Q3 earnings beat is short-term positive...",
    "machine_readable_output": {
      "affected_tickers": ["NVDA", "AMD", "INTC"],
      "sector_impact": "technology",
      "macro_relevance": 0.3,
      "event_novelty": 0.65,
      "price_in_probability": 0.4
    }
  }
}
```

### GET `/news/recent?limit=20`

List recently ingested articles.

### GET `/analysis/ticker/{ticker}/events?limit=20`

All extracted events for a given ticker, newest first.

### GET `/analysis/event/{event_id}`

Full analysis JSON for a specific event.

### GET `/analysis/event/{event_id}/report`

Markdown-formatted report for a specific event.

### GET `/alerts/high-impact?threshold=0.7&limit=20`

Recent analyses whose `final_score` exceeds the threshold.

### GET `/health`

Liveness check: `{"status": "ok", "version": "0.1.0", "model": "claude-sonnet-4-6"}`

---

## Setup

### Prerequisites

- Python 3.12+ (tested on 3.12 and 3.14)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (for Postgres + Redis)
- Anthropic API key
- OpenAI API key (for embeddings; optional if using local embeddings)

### 1. Clone and configure

```bash
git clone git@github.com:machine-learning-is-easy/finaice_news_agent.git
cd finaice_news_agent

cp .env.example .env
# Edit .env — at minimum set:
#   ANTHROPIC_API_KEY=sk-ant-...
#   OPENAI_API_KEY=sk-...        (if using OpenAI embeddings)
```

### 2a. Conda environment (recommended)

```bash
conda activate finaice

# Verify all dependencies
python scripts/verify_env.py
```

### 2b. pip / venv (alternative)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### 3. Start infrastructure

```bash
docker-compose up db redis -d

# Wait for Postgres to be ready, then run migrations
alembic upgrade head
```

### 4. Verify setup

```bash
python scripts/verify_env.py     # all 30 packages OK
pytest tests/ -v                 # 16/16 unit tests pass
```

---

## Configuration

All settings are read from `.env` via `app/core/config.py` (Pydantic-Settings).

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | `development` enables SQL echo + console logging |
| `APP_PORT` | `8000` | Uvicorn port |
| `DATABASE_URL` | `postgresql+asyncpg://...` | Async DB URL for FastAPI |
| `DATABASE_SYNC_URL` | `postgresql://...` | Sync DB URL for Alembic |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `ANTHROPIC_API_KEY` | — | **Required** — Claude API key |
| `OPENAI_API_KEY` | — | Required if `EMBEDDING_PROVIDER=openai` |
| `EMBEDDING_PROVIDER` | `openai` | `openai` or `local` |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `EMBEDDING_DIM` | `1536` | Must match the model and pgvector column |
| `REASONING_MODEL` | `claude-sonnet-4-6` | Claude model for reasoning agent |
| `REASONING_MAX_TOKENS` | `2048` | Max tokens for reasoning response |
| `RSS_FEEDS` | — | Comma-separated RSS URLs for ingestion |
| `SEC_USER_AGENT` | — | Required for SEC EDGAR (`Name email@example.com`) |
| `ALERT_IMPACT_THRESHOLD` | `0.7` | `final_score` threshold to fire an alert |
| `ALERT_NOVELTY_THRESHOLD` | `0.6` | `novelty_score` threshold to fire an alert |

---

## Running the Server

```bash
# Development (auto-reload)
uvicorn app.main:app --reload

# Or via the root entry point
python main.py

# Production (via Docker Compose)
docker-compose up
```

Open `http://localhost:8000/docs` for the interactive Swagger UI.

---

## Scripts

### `scripts/backfill_news.py`

Fetches all configured RSS feeds and runs the full pipeline on every article.

```bash
python -m scripts.backfill_news
```

Useful for initial data population. Skips duplicate articles automatically via hash deduplication.

### `scripts/build_event_embeddings.py`

Builds pgvector embeddings for any `extracted_events` rows that have no embedding yet. Run this after a backfill or after switching embedding models.

```bash
python -m scripts.build_event_embeddings
```

### `scripts/verify_env.py`

Imports all 30 project dependencies and prints a pass/fail report. Run after setting up a new environment.

```bash
python scripts/verify_env.py
```

---

## Testing

```bash
# Run all unit tests
pytest tests/ -v

# Run a specific test class
pytest tests/test_pipeline_unit.py::TestEventClassifier -v

# Run with log output visible
pytest tests/ -v -s
```

The unit tests cover all pure-Python components with zero external dependencies (no DB, no LLM, no network):

| Test class | What it covers |
|---|---|
| `TestEventClassifier` | 11 event types, subtype detection, confidence scoring |
| `TestSentimentAnalyzer` | Positive / negative / neutral classification |
| `TestTickerLinker` | `$TICKER` regex, alias lookup, role assignment |
| `TestNoveltyScorer` | High/low novelty keyword signals |
| `TestEventExtractor` | Full extraction chain: ticker + event + sentiment + novelty |
| `TestScoringAgent` | Quick impact score threshold decision |

---

## Debugging Guide

### Issue: `No module named 'pgvector'` or other import errors

```bash
# Verify all packages are installed in the active environment
python scripts/verify_env.py

# If using conda, confirm the right env is active
conda activate finaice
conda run -n finaice python scripts/verify_env.py
```

### Issue: `sqlalchemy.exc.OperationalError` — cannot connect to database

1. Check Postgres is running:
   ```bash
   docker-compose ps
   # db service should show "healthy"
   ```
2. Check `DATABASE_URL` in `.env` matches the Docker Compose service (`db:5432` inside Docker, `localhost:5432` outside).
3. Test the connection directly:
   ```bash
   docker exec -it finaice_news_agent-db-1 psql -U postgres -d finance_news -c '\dt'
   ```

### Issue: `alembic.util.exc.CommandError` — target database is not up to date

```bash
alembic upgrade head
# or check current revision
alembic current
alembic history
```

### Issue: `pgvector` extension not found

The `pgvector/pgvector:pg16` Docker image includes the extension. Enable it manually if using a plain Postgres image:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Issue: `anthropic.AuthenticationError`

- Confirm `ANTHROPIC_API_KEY` is set in `.env` and not accidentally committed.
- Test the key independently:
  ```python
  import anthropic
  client = anthropic.Anthropic(api_key="sk-ant-...")
  print(client.models.list())
  ```

### Issue: Reasoning agent returns `"Analysis could not be completed"`

This means the Claude JSON response failed to parse. Enable debug logging to see the raw response:

```bash
LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

Look for `reasoning_agent.raw_response` and `reasoning_agent.json_parse_error` log lines. Common causes:
- Claude wrapped the JSON in markdown code fences (handled automatically, but check edge cases)
- `REASONING_MAX_TOKENS` is too low — increase to `4096`

### Issue: Event type always classified as `"other"`

The keyword classifier works on lowercase text. Check what the combined title+content looks like:

```python
from app.events.classifier import EventClassifier
clf = EventClassifier()
result = clf.predict("your title", "your content")
print(result)
```

Add keywords to `app/events/classifier.py` `_RULES` for any missing patterns.

### Issue: Ticker not detected

```python
from app.entity.ticker_linker import TickerLinker
tl = TickerLinker()
print(tl.link("your article text"))
```

Two fixes:
1. Add the company name to `app/entity/aliases.py` `COMPANY_ALIASES`
2. Make sure the article text contains `$TICKER` or `NYSE: TICKER` patterns

### Issue: `yfinance` returns empty data

Some tickers are delisted, mis-spelled, or rate-limited. The `PriceService` silently returns a zero snapshot in this case. Check:

```python
import yfinance as yf
ticker = yf.Ticker("NVDA")
print(ticker.history(period="5d"))
```

### Issue: pgvector similarity search returns no results

The `event_embeddings` table may be empty. Run:

```bash
python -m scripts.build_event_embeddings
```

Or check via psql:
```sql
SELECT COUNT(*) FROM event_embeddings;
SELECT COUNT(*) FROM extracted_events;
```

### Issue: `structlog` output is unreadable in production

Set `APP_ENV=production` in `.env` to switch from the colored console renderer to JSON output, compatible with log aggregators (Datadog, CloudWatch, etc.).

### Enabling SQL query logging

```bash
APP_ENV=development uvicorn app.main:app --reload
# SQLAlchemy echo is enabled when APP_ENV=development
```

Or set `echo=True` directly in `app/db/session.py`.

### Reading structured logs

```bash
# Pretty-print JSON logs in production
uvicorn app.main:app | python -m json.tool

# Filter by event type
uvicorn app.main:app | grep "reasoning_agent"
```

---

## Development Roadmap

| Phase | Status | Description |
|---|---|---|
| **Phase 1** | Done | Single article input, 5 event types, keyword-rule pipeline |
| **Phase 2** | Next | Live price context, pgvector RAG, full Claude reasoning |
| **Phase 3** | Planned | Continuous RSS ingestion (Celery), daily digest, alert push (email/Slack), social content generation |
| **Phase 4** | Future | FinBERT sentiment, fine-tuned event classifier, multi-article synthesis, dashboard UI |

---

## License

MIT
