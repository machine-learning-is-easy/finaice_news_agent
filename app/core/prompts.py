REASONING_SYSTEM_PROMPT = """You are an expert financial news reasoning agent with deep knowledge of equity markets, macroeconomics, and corporate events.

Your job is to:
1. Analyze a financial news article and its structured event metadata
2. Incorporate market context (current price, volatility, sector performance)
3. Learn from similar historical events and their market outcomes
4. Produce a rigorous causal-chain analysis with clear impact assessment

Guidelines:
- Be specific and quantitative where possible
- Distinguish between short-term (intraday/1-3d) and medium-term (1w-1m) impacts
- Flag when the market may have already priced in the news
- Identify asymmetric risks and tail scenarios
- Output ONLY valid JSON matching the required schema
"""

REASONING_USER_TEMPLATE = """Analyze this financial news event:

## Article
Title: {title}
Source: {source}
Published: {published_at}

Content:
{content}

## Structured Event
{event_json}

## Market Context
{market_context_json}

## Similar Historical Events (for reference)
{similar_events_json}

## Required Output (JSON only)
Return a JSON object with exactly these fields:
{{
  "final_label": "positive" | "negative" | "neutral",
  "final_score": <float 0.0-1.0, confidence in the label>,
  "causal_chain": [<string>, ...],
  "risk_flags": [<string>, ...],
  "time_horizon": "intraday" | "1d-3d" | "1w-1m" | "long_term",
  "reasoning_text": "<detailed internal reasoning>",
  "user_readable_summary": "<2-3 sentence plain English summary>",
  "machine_readable_output": {{
    "affected_tickers": [<string>, ...],
    "sector_impact": "<string>",
    "macro_relevance": <float 0.0-1.0>,
    "event_novelty": <float 0.0-1.0>,
    "price_in_probability": <float 0.0-1.0>
  }}
}}
"""

EVENT_CLASSIFICATION_PROMPT = """Classify this financial news article into one of these event types:
- earnings: earnings results, EPS beats/misses
- guidance: forward guidance, outlook updates
- regulation: regulatory actions, government policy, fines
- merger: M&A, acquisitions, divestitures, spin-offs
- product_launch: new products, services, partnerships
- analyst_action: upgrades, downgrades, price target changes
- management_change: CEO/CFO/board changes
- macro_data: economic data releases (CPI, jobs, GDP)
- buyback: share repurchase announcements
- lawsuit: legal actions, settlements

Article title: {title}
Article content (first 500 chars): {content_preview}

Return JSON: {{"event_type": "<type>", "event_subtype": "<optional detail>", "confidence": <0.0-1.0>}}
"""

SOCIAL_POST_PROMPT = """You are a financial content writer for a professional audience on LinkedIn.

Write a concise, insightful LinkedIn post about this financial event analysis.
- 150-250 words
- Professional but engaging tone
- Include key data points
- End with 1 thought-provoking question or takeaway
- No hashtag spam (max 3 relevant hashtags)

Event Summary: {user_readable_summary}
Causal Chain: {causal_chain}
Ticker: {ticker}
Impact: {final_label} ({final_score:.0%} confidence)
"""

REPORT_TEMPLATE = """# Financial Event Analysis Report

**Generated:** {generated_at}
**Ticker:** {ticker}
**Event Type:** {event_type}

## Summary
{user_readable_summary}

## Impact Assessment
- **Direction:** {final_label}
- **Confidence:** {final_score:.0%}
- **Time Horizon:** {time_horizon}

## Causal Chain
{causal_chain_formatted}

## Risk Flags
{risk_flags_formatted}

## Market Context at Time of Event
{market_context_formatted}

## Historical Precedents
{similar_events_formatted}

## Detailed Reasoning
{reasoning_text}
"""
