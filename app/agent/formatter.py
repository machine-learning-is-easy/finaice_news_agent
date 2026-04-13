"""
Formats AgentAnalysis into various output formats.
"""
from datetime import datetime, timezone
from app.agent.schemas import AgentAnalysis, ExtractedEvent
from app.core.prompts import REPORT_TEMPLATE


class AnalysisFormatter:
    def to_markdown_report(
        self,
        analysis: AgentAnalysis,
        event: ExtractedEvent,
    ) -> str:
        causal = "\n".join(f"{i+1}. {step}" for i, step in enumerate(analysis.causal_chain))
        risks = "\n".join(f"- {flag}" for flag in analysis.risk_flags)
        market_lines = (
            f"- Ticker: {event.primary_ticker}\n"
            f"- Event Type: {event.event_type}\n"
            f"- Sentiment: {event.sentiment_label} ({event.sentiment_score:.0%})\n"
            f"- Novelty: {event.novelty_score:.0%}"
        )
        similar_lines = "No historical precedents retrieved."

        return REPORT_TEMPLATE.format(
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            ticker=event.primary_ticker or "N/A",
            event_type=event.event_type,
            user_readable_summary=analysis.user_readable_summary,
            final_label=analysis.final_label,
            final_score=analysis.final_score,
            time_horizon=analysis.time_horizon,
            causal_chain_formatted=causal,
            risk_flags_formatted=risks,
            market_context_formatted=market_lines,
            similar_events_formatted=similar_lines,
            reasoning_text=analysis.reasoning_text,
        )

    def to_short_alert(self, analysis: AgentAnalysis, ticker: str | None) -> str:
        direction_emoji = {"positive": "[+]", "negative": "[-]", "neutral": "[~]"}
        prefix = direction_emoji.get(analysis.final_label, "[?]")
        ticker_str = f"${ticker}" if ticker else "market"
        return (
            f"{prefix} {ticker_str} | {analysis.final_label.upper()} "
            f"({analysis.final_score:.0%} confidence) | {analysis.time_horizon}\n"
            f"{analysis.user_readable_summary}"
        )
