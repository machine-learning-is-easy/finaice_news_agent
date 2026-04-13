"""
Report generator: builds markdown/HTML reports from analysis results.
"""
from app.agent.schemas import AgentAnalysis, ExtractedEvent
from app.agent.formatter import AnalysisFormatter
from app.core.logging import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    def __init__(self):
        self.formatter = AnalysisFormatter()

    def generate_markdown(self, analysis: AgentAnalysis, event: ExtractedEvent) -> str:
        return self.formatter.to_markdown_report(analysis, event)

    def generate_daily_digest(self, items: list[tuple[ExtractedEvent, AgentAnalysis]]) -> str:
        if not items:
            return "# Daily Digest\n\nNo significant events today."

        lines = ["# Daily Financial Event Digest\n"]
        for event, analysis in sorted(items, key=lambda x: -x[1].final_score):
            ticker = event.primary_ticker or "N/A"
            label = analysis.final_label.upper()
            score = f"{analysis.final_score:.0%}"
            summary = analysis.user_readable_summary
            lines.append(f"## ${ticker} — {event.event_type} [{label} {score}]")
            lines.append(f"{summary}\n")

        return "\n".join(lines)
