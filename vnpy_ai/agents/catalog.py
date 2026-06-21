"""
Dependency-light analyst catalog.

Source inspiration: AI Hedge Fund by Virat Singh (MIT License).
"""

from __future__ import annotations

from typing import Any


ANALYST_ORDER = [
    ("Aswath Damodaran", "aswath_damodaran"),
    ("Ben Graham", "ben_graham"),
    ("Bill Ackman", "bill_ackman"),
    ("Cathie Wood", "cathie_wood"),
    ("Charlie Munger", "charlie_munger"),
    ("Michael Burry", "michael_burry"),
    ("Mohnish Pabrai", "mohnish_pabrai"),
    ("Nassim Taleb", "nassim_taleb"),
    ("Peter Lynch", "peter_lynch"),
    ("Phil Fisher", "phil_fisher"),
    ("Rakesh Jhunjhunwala", "rakesh_jhunjhunwala"),
    ("Stanley Druckenmiller", "stanley_druckenmiller"),
    ("Warren Buffett", "warren_buffett"),
    ("Technical Analyst", "technical_analyst"),
    ("Fundamentals Analyst", "fundamentals_analyst"),
    ("Growth Analyst", "growth_analyst"),
    ("News Sentiment Analyst", "news_sentiment_analyst"),
    ("Sentiment Analyst", "sentiment_analyst"),
    ("Valuation Analyst", "valuation_analyst"),
]


def get_agents_list() -> list[dict[str, Any]]:
    """Return analyst metadata for UI and API consumers."""

    return [
        {
            "key": key,
            "display_name": display_name,
            "description": "AI Hedge Fund analyst",
            "investing_style": "Runs inside the isolated AI Agent workflow when optional dependencies are installed.",
            "order": index,
        }
        for index, (display_name, key) in enumerate(ANALYST_ORDER)
    ]


def get_agent_catalog() -> dict[str, dict[str, Any]]:
    """Return a full agent catalog keyed by agent key for runtime lookup."""

    return {key: entry for key, entry in zip(
        [k for _, k in ANALYST_ORDER],
        get_agents_list(), strict=False,
    )}

