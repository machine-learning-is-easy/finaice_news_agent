"""
Text cleaning utilities for raw news content.
"""
import re
import html


def clean_html(raw: str) -> str:
    raw = html.unescape(raw)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return raw


def normalize_whitespace(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_article_text(text: str) -> str:
    text = clean_html(text)
    text = normalize_whitespace(text)
    # Remove common boilerplate footers
    for pattern in [
        r"©\s*\d{4}.*",
        r"All rights reserved.*",
        r"Subscribe to.*newsletter.*",
        r"Click here to.*",
    ]:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)
    return text.strip()


def truncate(text: str, max_chars: int = 8000) -> str:
    return text[:max_chars]
