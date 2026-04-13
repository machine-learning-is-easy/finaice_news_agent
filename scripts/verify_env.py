"""Run this to verify all project dependencies are installed correctly."""
import sys

checks = []
failures = []

def check(label, fn):
    try:
        result = fn()
        checks.append(f"  [OK] {label}" + (f" — {result}" if result else ""))
    except Exception as e:
        failures.append(f"  [FAIL] {label} — {e}")

# Core
check("pydantic",         lambda: __import__("pydantic").__version__)
check("pydantic-settings",lambda: __import__("pydantic_settings").__version__)
check("fastapi",          lambda: __import__("fastapi").__version__)
check("uvicorn",          lambda: __import__("uvicorn").__version__)

# Database
check("sqlalchemy",       lambda: __import__("sqlalchemy").__version__)
check("asyncpg",          lambda: __import__("asyncpg").__version__)
check("psycopg2",         lambda: __import__("psycopg2").__version__)
check("alembic",          lambda: __import__("alembic").__version__)
check("pgvector",         lambda: __import__("importlib.metadata").metadata.version("pgvector"))

# Cache
check("redis",            lambda: __import__("redis").__version__)
check("hiredis",          lambda: __import__("hiredis").__version__)

# HTTP / RSS
check("httpx",            lambda: __import__("httpx").__version__)
check("feedparser",       lambda: __import__("feedparser").__version__)
check("beautifulsoup4",   lambda: __import__("bs4").__version__)
check("lxml",             lambda: __import__("lxml").__version__)

# LLM
check("anthropic",        lambda: __import__("anthropic").__version__)
check("openai",           lambda: __import__("openai").__version__)

# Finance / ML
check("yfinance",         lambda: __import__("yfinance").__version__)
check("numpy",            lambda: __import__("numpy").__version__)
check("scikit-learn",     lambda: __import__("sklearn").__version__)

# NLP
check("spacy",            lambda: __import__("spacy").__version__)
check("en_core_web_sm",   lambda: __import__("spacy").load("en_core_web_sm") and "loaded")

# Async tasks
check("celery",           lambda: __import__("celery").__version__)
check("kombu",            lambda: __import__("kombu").__version__)

# Utils
check("structlog",        lambda: __import__("structlog").__version__)
check("python-dotenv",    lambda: __import__("importlib.metadata").metadata.version("python-dotenv"))
check("tenacity",         lambda: __import__("importlib.metadata").metadata.version("tenacity"))
check("arrow",            lambda: __import__("arrow").__version__)

# Testing
check("pytest",           lambda: __import__("pytest").__version__)
check("pytest-asyncio",   lambda: __import__("pytest_asyncio").__version__)

print(f"Python {sys.version}\n")
print("\n".join(checks))
if failures:
    print("\n--- MISSING ---")
    print("\n".join(failures))
    sys.exit(1)
else:
    print(f"\nAll {len(checks)} packages verified successfully.")
