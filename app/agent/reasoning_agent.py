"""
Core reasoning agent powered by Claude (Anthropic API).
Implements prompt caching for efficiency on repeated system prompts.
"""
import json
from typing import Optional

import anthropic

from app.agent.schemas import (
    NewsArticle, ExtractedEvent, MarketContext,
    SimilarEvent, AgentAnalysis, MachineReadableOutput,
)
from app.core.config import get_settings
from app.core.prompts import REASONING_SYSTEM_PROMPT, REASONING_USER_TEMPLATE
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class ReasoningAgent:
    """
    Calls Claude to perform causal-chain financial analysis.
    Uses prompt caching on the system prompt to reduce latency and cost.
    """

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.reasoning_model
        self.max_tokens = settings.reasoning_max_tokens

    def analyze(
        self,
        article: NewsArticle,
        event: ExtractedEvent,
        market_context: Optional[MarketContext],
        similar_events: list[SimilarEvent],
    ) -> AgentAnalysis:
        prompt = self._build_user_prompt(article, event, market_context, similar_events)

        logger.info(
            "reasoning_agent.calling_claude",
            ticker=event.primary_ticker,
            event_type=event.event_type,
            model=self.model,
        )

        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[
                {
                    "type": "text",
                    "text": REASONING_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # prompt caching
                }
            ],
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()
        logger.debug("reasoning_agent.raw_response", length=len(raw_text))

        return self._parse_response(raw_text)

    def _build_user_prompt(
        self,
        article: NewsArticle,
        event: ExtractedEvent,
        market_context: Optional[MarketContext],
        similar_events: list[SimilarEvent],
    ) -> str:
        market_json = market_context.model_dump_json(indent=2) if market_context else "null"
        similar_json = json.dumps(
            [s.model_dump() for s in similar_events], indent=2
        ) if similar_events else "[]"

        return REASONING_USER_TEMPLATE.format(
            title=article.title,
            source=article.source,
            published_at=article.published_at.isoformat(),
            content=article.content[:3000],
            event_json=event.model_dump_json(indent=2, exclude={"entities"}),
            market_context_json=market_json,
            similar_events_json=similar_json,
        )

    def _parse_response(self, raw_text: str) -> AgentAnalysis:
        # Strip markdown code fences if present
        text = raw_text
        if "```" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            text = text[start:end]

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("reasoning_agent.json_parse_error", error=str(e), raw=text[:300])
            return self._fallback_analysis()

        machine = data.get("machine_readable_output", {})
        return AgentAnalysis(
            final_label=data.get("final_label", "neutral"),
            final_score=float(data.get("final_score", 0.5)),
            causal_chain=data.get("causal_chain", []),
            risk_flags=data.get("risk_flags", []),
            time_horizon=data.get("time_horizon", "1d-3d"),
            reasoning_text=data.get("reasoning_text", ""),
            user_readable_summary=data.get("user_readable_summary", ""),
            machine_readable_output=MachineReadableOutput(
                affected_tickers=machine.get("affected_tickers", []),
                sector_impact=machine.get("sector_impact", ""),
                macro_relevance=float(machine.get("macro_relevance", 0.0)),
                event_novelty=float(machine.get("event_novelty", 0.0)),
                price_in_probability=float(machine.get("price_in_probability", 0.0)),
            ),
        )

    def _fallback_analysis(self) -> AgentAnalysis:
        return AgentAnalysis(
            final_label="neutral",
            final_score=0.5,
            causal_chain=["Analysis unavailable due to parsing error."],
            risk_flags=["LLM response could not be parsed."],
            time_horizon="1d-3d",
            reasoning_text="Fallback: JSON parse failed.",
            user_readable_summary="Analysis could not be completed. Please retry.",
            machine_readable_output=MachineReadableOutput(),
        )
