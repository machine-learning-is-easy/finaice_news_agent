"""
Social content writer: generates LinkedIn posts and video scripts from analysis.
"""
import json
from app.agent.schemas import AgentAnalysis, ExtractedEvent
from app.core.config import get_settings
from app.core.prompts import SOCIAL_POST_PROMPT
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class SocialWriter:
    def __init__(self):
        import anthropic
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def write_linkedin_post(self, event: ExtractedEvent, analysis: AgentAnalysis) -> str:
        prompt = SOCIAL_POST_PROMPT.format(
            user_readable_summary=analysis.user_readable_summary,
            causal_chain="\n".join(f"- {s}" for s in analysis.causal_chain),
            ticker=event.primary_ticker or "market",
            final_label=analysis.final_label,
            final_score=analysis.final_score,
        )

        response = self._client.messages.create(
            model=settings.reasoning_model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        post = response.content[0].text.strip()
        logger.info("social_writer.linkedin_post_generated", ticker=event.primary_ticker)
        return post

    def write_video_script(self, event: ExtractedEvent, analysis: AgentAnalysis) -> str:
        """
        Generates a short-form video script (60-90 seconds).
        """
        prompt = f"""Write a 60-second financial news video script about this event.
Format: Hook → Context → Key Facts → Impact → Call to Action.
Keep it conversational and punchy.

Ticker: {event.primary_ticker}
Event: {event.event_type}
Summary: {analysis.user_readable_summary}
Impact: {analysis.final_label} ({analysis.final_score:.0%})
Causal chain: {chr(10).join(analysis.causal_chain)}
"""
        response = self._client.messages.create(
            model=settings.reasoning_model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
