# Agent Setup Guide

Step-by-step instructions to get the Finance News Agent running and sending email alerts to your inbox.

---

## What the agent does

1. You start it and enter your email
2. It asks for your SMTP credentials (Gmail App Password)
3. It polls financial RSS feeds every 5 minutes
4. For each new article it scores the impact — low-signal news is skipped
5. For significant news it calls Claude to produce a causal-chain analysis
6. It composes an HTML email and sends it directly to you

---

## Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.12+ | Tested on 3.12 and 3.14 |
| Conda (recommended) | Or plain pip/venv |
| Anthropic API key | Required — powers the reasoning agent |
| Gmail account | Used to send alert emails |
| Gmail App Password | A 16-character password for SMTP access |

---

## Step 1 — Clone the repo

```bash
git clone git@github.com:machine-learning-is-easy/finaice_news_agent.git
cd finaice_news_agent
```

---

## Step 2 — Activate the conda environment

```bash
conda activate finaice
```

If the environment does not exist yet, create it and install dependencies:

```bash
conda create -n finaice python=3.12 -y
conda activate finaice
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Verify everything installed correctly:

```bash
python scripts/verify_env.py
```

All 30 packages should show `[OK]`.

---

## Step 3 — Configure your API key

Copy the example env file:

```bash
cp .env.example .env
```

Open `.env` and set your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

This is the only field that is strictly required to run the agent.

---

## Step 4 — Get a Gmail App Password

The agent sends emails via Gmail SMTP. Gmail requires an **App Password** instead of your regular password.

1. Go to your Google Account → **Security**
2. Under "How you sign in to Google", enable **2-Step Verification** if not already on
3. Go to **App Passwords**: https://myaccount.google.com/apppasswords
4. Select app → **Mail**, device → **Other**, name it `Finance Agent`
5. Click **Generate** — copy the 16-character password shown

You will enter this password when the agent starts, or you can save it in `.env`:

```
SMTP_USER=you@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop
```

If set in `.env`, the agent will skip asking for SMTP credentials on startup.

---

## Step 5 — Run the agent

```bash
python agent.py
```

You will see an interactive prompt:

```
====================================================
  Finance News Agent
====================================================

  Where should alerts be sent?
  Your email address: you@gmail.com

  SMTP credentials (used to send emails on your behalf)
  Tip: for Gmail, use an App Password
  SMTP username (Gmail address): you@gmail.com
  SMTP password / App Password: ················

  Poll interval in seconds [300]:
  Minimum impact score to trigger email 0.0–1.0 [0.5]:
```

Press **Enter** to accept defaults, or enter your preferred values.

Once configured, the agent starts immediately:

```
[Agent] Listening to 3 feed(s):
  https://feeds.reuters.com/reuters/businessNews
  https://feeds.reuters.com/reuters/technologyNews
  https://finance.yahoo.com/news/rssindex
[Agent] Poll interval : 300s
[Agent] Min score     : 0.5
[Agent] Alerts → you@gmail.com
[Agent] Press Ctrl+C to stop.

[09:15:00] Fetching news...
  → [EARNINGS] Nvidia beats Q3 estimates (score=0.82, ticker=NVDA)
  ✓ Email sent — POSITIVE (87%) | Nvidia's Q3 beat is short-term positive...
[09:15:00] 42 articles fetched, 38 new.
[Agent] Next check in 300s...
```

Press **Ctrl+C** at any time to stop.

---

## Skip the questions with flags

Pass arguments directly to skip the interactive prompts:

```bash
python agent.py --email you@gmail.com --interval 180 --score 0.6
```

| Flag | Description | Default |
|---|---|---|
| `--email` | Recipient email address | Asked interactively |
| `--interval` | Poll interval in seconds | `300` |
| `--score` | Minimum impact score to trigger email (0.0–1.0) | `0.5` |

---

## Email alert format

Each alert email looks like this:

**Subject:**
```
📈 [NVDA] POSITIVE (87%) — earnings
```

**Body:**

```
┌─────────────────────────────────────────────┐
│ 📈  $NVDA — POSITIVE                        │
│ Confidence 87% · 1d-3d horizon              │
└─────────────────────────────────────────────┘

SUMMARY
Nvidia's Q3 earnings beat is short-term positive.
Raised guidance signals sustained AI chip demand...

CAUSAL CHAIN
1. EPS beat drives upward revision in analyst estimates
2. Raised guidance signals sustained AI chip demand
3. Positive revisions typically expand P/E multiples

RISK FLAGS
- Elevated valuation may limit upside despite the beat
- Export control uncertainty could weigh on guidance credibility

EVENT DETAILS
Ticker       $NVDA
Event type   earnings
Sentiment    positive (95%)
Novelty      65%
Time horizon 1d-3d
```

---

## Tuning the impact score threshold

The `--score` flag (or `ALERT_IMPACT_THRESHOLD` in `.env`) controls how selective the agent is.

| Score | Effect |
|---|---|
| `0.3` | Sends emails for most news — high volume |
| `0.5` | Balanced — significant events only (recommended) |
| `0.7` | High-impact only — major earnings beats, mergers, crises |
| `0.9` | Almost nothing — extreme events only |

---

## Add your own RSS feeds

Edit `.env` and add a comma-separated list:

```
RSS_FEEDS=https://feeds.reuters.com/reuters/businessNews,https://finance.yahoo.com/news/rssindex,https://feeds.bloomberg.com/markets/news.rss
```

If `RSS_FEEDS` is empty, the agent uses these defaults:
- Reuters Business News
- Reuters Technology News
- Yahoo Finance

---

## Run as a background process (optional)

**Windows — run in a new terminal window:**
```bash
start python agent.py --email you@gmail.com
```

**Linux / Mac — run in background with nohup:**
```bash
nohup python agent.py --email you@gmail.com > agent.log 2>&1 &
```

**Keep it running with a process manager (recommended for long-term use):**
```bash
# Install PM2
npm install -g pm2

# Start the agent
pm2 start "python agent.py --email you@gmail.com" --name finance-agent

# View logs
pm2 logs finance-agent

# Stop
pm2 stop finance-agent
```

---

## Troubleshooting

### `ANTHROPIC_API_KEY is not set`
Open `.env` and add:
```
ANTHROPIC_API_KEY=sk-ant-...
```

### `Email FAILED` in the console
- Make sure you used an **App Password**, not your regular Gmail password
- Confirm 2-Step Verification is enabled on your Google account
- Check `SMTP_HOST=smtp.gmail.com` and `SMTP_PORT=587` in `.env`
- Test your credentials manually:
  ```python
  import smtplib
  with smtplib.SMTP("smtp.gmail.com", 587) as s:
      s.starttls()
      s.login("you@gmail.com", "your_app_password")
      print("Login OK")
  ```

### No emails arriving but agent is running
- Check your spam / junk folder
- Lower the score threshold: `python agent.py --score 0.3`
- Watch the console — lines starting with `→` are articles being processed

### `ModuleNotFoundError`
The wrong Python environment is active. Run:
```bash
conda activate finaice
python scripts/verify_env.py
```

### Agent stops after one poll
This should not happen — check the console for a traceback and report the error message.
