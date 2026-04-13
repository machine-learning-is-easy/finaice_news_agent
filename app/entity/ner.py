"""
Named entity recognition wrapper.
Uses spaCy for person/org extraction.
Falls back gracefully if spaCy model is not installed.
"""
from typing import Optional

try:
    import spacy
    _nlp = spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except Exception:
    _nlp = None
    SPACY_AVAILABLE = False

from app.core.logging import get_logger

logger = get_logger(__name__)


class NERExtractor:
    def extract_organizations(self, text: str) -> list[str]:
        if not SPACY_AVAILABLE or _nlp is None:
            return []
        doc = _nlp(text[:5000])  # limit for performance
        return list({ent.text for ent in doc.ents if ent.label_ in ("ORG", "PRODUCT")})

    def extract_persons(self, text: str) -> list[str]:
        if not SPACY_AVAILABLE or _nlp is None:
            return []
        doc = _nlp(text[:5000])
        return list({ent.text for ent in doc.ents if ent.label_ == "PERSON"})

    def is_available(self) -> bool:
        return SPACY_AVAILABLE
