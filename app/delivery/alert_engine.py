"""
Alert engine: decides which events warrant a high-priority alert.
Extensible to send alerts via email, Slack, webhook, etc.
"""
from app.agent.schemas import AgentAnalysis, ExtractedEvent
from app.agent.formatter import AnalysisFormatter
from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


class AlertEngine:
    def __init__(self):
        self.formatter = AnalysisFormatter()
        self.impact_threshold = settings.alert_impact_threshold
        self.novelty_threshold = settings.alert_novelty_threshold

    def should_alert(self, event: ExtractedEvent, analysis: AgentAnalysis) -> bool:
        return (
            analysis.final_score >= self.impact_threshold
            or event.novelty_score >= self.novelty_threshold
        )

    def fire_alert(self, event: ExtractedEvent, analysis: AgentAnalysis) -> dict:
        message = self.formatter.to_short_alert(analysis, event.primary_ticker)
        alert = {
            "ticker": event.primary_ticker,
            "event_type": event.event_type,
            "final_label": analysis.final_label,
            "final_score": analysis.final_score,
            "message": message,
        }
        logger.info("alert_engine.fired", **{k: v for k, v in alert.items() if k != "message"})

        # Hook point: add email / Slack / webhook delivery here
        self._log_to_console(message)
        return alert

    def _log_to_console(self, message: str) -> None:
        print("\n=== ALERT ===")
        print(message)
        print("=" * 40)
