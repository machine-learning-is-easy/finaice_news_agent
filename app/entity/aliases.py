"""
Static alias map: company name / brand / product → ticker.
Extend this map as needed or load from a database table.
"""

COMPANY_ALIASES: dict[str, str] = {
    # Big Tech
    "apple": "AAPL",
    "microsoft": "MSFT",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "amazon": "AMZN",
    "meta": "META",
    "facebook": "META",
    "nvidia": "NVDA",
    "tesla": "TSLA",
    "netflix": "NFLX",
    "salesforce": "CRM",
    "adobe": "ADBE",
    "intel": "INTC",
    "amd": "AMD",
    "qualcomm": "QCOM",
    "broadcom": "AVGO",
    "ibm": "IBM",
    "oracle": "ORCL",
    "cisco": "CSCO",
    # Finance
    "jpmorgan": "JPM",
    "jp morgan": "JPM",
    "bank of america": "BAC",
    "goldman sachs": "GS",
    "morgan stanley": "MS",
    "wells fargo": "WFC",
    "citigroup": "C",
    "blackrock": "BLK",
    "berkshire": "BRK-B",
    "berkshire hathaway": "BRK-B",
    "visa": "V",
    "mastercard": "MA",
    "american express": "AXP",
    "paypal": "PYPL",
    # Healthcare
    "johnson & johnson": "JNJ",
    "johnson and johnson": "JNJ",
    "pfizer": "PFE",
    "moderna": "MRNA",
    "unitedhealth": "UNH",
    "abbvie": "ABBV",
    "merck": "MRK",
    "eli lilly": "LLY",
    # Consumer
    "walmart": "WMT",
    "target": "TGT",
    "costco": "COST",
    "mcdonalds": "MCD",
    "starbucks": "SBUX",
    "coca-cola": "KO",
    "coca cola": "KO",
    "pepsi": "PEP",
    "pepsico": "PEP",
    "disney": "DIS",
    # Energy
    "exxon": "XOM",
    "exxonmobil": "XOM",
    "chevron": "CVX",
    # ETFs / Indices
    "spy": "SPY",
    "qqq": "QQQ",
    "s&p 500": "SPY",
    "nasdaq": "QQQ",
}

# Sector ETF map: sector name → ETF ticker
SECTOR_ETFS: dict[str, str] = {
    "technology": "XLK",
    "financials": "XLF",
    "healthcare": "XLV",
    "energy": "XLE",
    "consumer discretionary": "XLY",
    "consumer staples": "XLP",
    "industrials": "XLI",
    "materials": "XLB",
    "real estate": "XLRE",
    "utilities": "XLU",
    "communication services": "XLC",
}

# Ticker → sector mapping (subset)
TICKER_SECTOR: dict[str, str] = {
    "AAPL": "technology", "MSFT": "technology", "GOOGL": "technology",
    "AMZN": "technology", "META": "technology", "NVDA": "technology",
    "TSLA": "consumer discretionary", "NFLX": "communication services",
    "JPM": "financials", "BAC": "financials", "GS": "financials",
    "MS": "financials", "WFC": "financials", "C": "financials",
    "JNJ": "healthcare", "PFE": "healthcare", "MRNA": "healthcare",
    "UNH": "healthcare", "ABBV": "healthcare", "LLY": "healthcare",
    "XOM": "energy", "CVX": "energy",
    "WMT": "consumer staples", "KO": "consumer staples", "PEP": "consumer staples",
}
