"""Mock agent outputs for testing."""
MOCK_BUFFETT_OUTPUT = {
    "agent_id": "warren_buffett",
    "ticker": "AAPL",
    "signal": "buy",
    "confidence": 85,
    "reasoning": "Strong moat and consistent earnings growth.",
}

MOCK_GRAHAM_OUTPUT = {
    "agent_id": "benjamin_graham",
    "ticker": "AAPL",
    "signal": "hold",
    "confidence": 50,
    "reasoning": "Price above intrinsic value.",
}

MOCK_RISK_OUTPUT = {
    "max_position_size": 0.1,
    "risk_score": 3,
    "warnings": [],
}

MOCK_PORTFOLIO_OUTPUT = {
    "decisions": [
        {"ticker": "AAPL", "action": "buy", "quantity": 100, "confidence": 80},
        {"ticker": "GOOGL", "action": "hold", "quantity": 0, "confidence": 50},
    ]
}

MOCK_PRICES = {
    "AAPL": [{"date": "2024-01-01", "close": 185.0}, {"date": "2024-01-02", "close": 186.5}],
    "GOOGL": [{"date": "2024-01-01", "close": 140.0}, {"date": "2024-01-02", "close": 141.2}],
}

MOCK_FINANCIAL_METRICS = {
    "AAPL": {
        "market_cap": 2800000000000,
        "pe_ratio": 28.5,
        "pb_ratio": 45.2,
        "roe": 0.45,
        "debt_to_equity": 1.8,
    }
}