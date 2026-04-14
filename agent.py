"""
Finance News Agent — interactive CLI entry point.

Usage:
    python agent.py
    python agent.py --email you@gmail.com --interval 300
"""
import argparse
import getpass
import os
import re
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.logging import setup_logging
from app.core.config import get_settings

setup_logging()
settings = get_settings()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _ask_email() -> str:
    while True:
        email = input("  Your email address: ").strip()
        if _EMAIL_RE.match(email):
            return email
        print("  Invalid email. Please try again.")


def _ask_smtp() -> tuple[str, str]:
    """Returns (smtp_user, smtp_password). Uses .env values if already set."""
    user = settings.smtp_user
    password = settings.smtp_password

    if user and password:
        print(f"  Using SMTP credentials from .env ({user})")
        return user, password

    print("\n  SMTP credentials (used to send emails on your behalf)")
    print("  Tip: for Gmail, use an App Password — https://myaccount.google.com/apppasswords")
    user = input("  SMTP username (Gmail address): ").strip()
    password = getpass.getpass("  SMTP password / App Password: ")
    return user, password


def _ask_interval() -> int:
    val = input("  Poll interval in seconds [300]: ").strip()
    if not val:
        return 300
    try:
        n = int(val)
        return max(60, n)
    except ValueError:
        print("  Invalid input, using 300s.")
        return 300


def _ask_min_score() -> float:
    val = input("  Minimum impact score to trigger email 0.0–1.0 [0.5]: ").strip()
    if not val:
        return 0.5
    try:
        f = float(val)
        return max(0.0, min(1.0, f))
    except ValueError:
        print("  Invalid input, using 0.5.")
        return 0.5


def _check_api_key() -> None:
    if not settings.anthropic_api_key:
        print("\n[Error] ANTHROPIC_API_KEY is not set.")
        print("  Add it to your .env file:  ANTHROPIC_API_KEY=sk-ant-...")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Finance News Agent — monitors RSS feeds and emails analysis to you."
    )
    parser.add_argument("--email",    help="Recipient email address")
    parser.add_argument("--interval", type=int, help="Poll interval in seconds (default 300)")
    parser.add_argument("--score",    type=float, help="Min impact score 0.0-1.0 (default 0.5)")
    args = parser.parse_args()

    _check_api_key()

    print("=" * 52)
    print("  Finance News Agent")
    print("=" * 52)

    # 1. Get recipient email
    if args.email and _EMAIL_RE.match(args.email):
        recipient = args.email
        print(f"\n  Sending alerts to: {recipient}")
    else:
        print("\n  Where should alerts be sent?")
        recipient = _ask_email()

    # 2. Get SMTP credentials
    smtp_user, smtp_password = _ask_smtp()

    # 3. Poll interval
    interval = args.interval or _ask_interval()

    # 4. Minimum score
    min_score = args.score if args.score is not None else _ask_min_score()

    print(f"\n[Agent] Starting up...")
    print(f"[Agent] Alerts → {recipient}")
    print(f"[Agent] Poll every {interval}s | min score {min_score}")

    # 5. Launch the listener
    from app.agent.news_listener import NewsListener
    from app.delivery.email_sender import EmailSender

    listener = NewsListener(
        recipient_email=recipient,
        poll_interval=interval,
        min_score=min_score,
    )

    # Inject the SMTP credentials collected interactively
    listener.email_sender = EmailSender(
        recipient=recipient,
        smtp_user=smtp_user,
        smtp_password=smtp_password,
    )

    listener.start()


if __name__ == "__main__":
    main()
