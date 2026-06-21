"""
Analyst registry for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/analysts.py (MIT License, Virat Singh).
Import paths are rewritten to reference `vnpy_ai.agents` classes instead of
the upstream `src.agents` functions. Agent classes inherit from `AgentBase`
and must be instantiated with a `DataAdapter` before use.
"""

from __future__ import annotations

from typing import Any

from vnpy_ai.agents.aswath_damodaran import AswathDamodaranAgent
from vnpy_ai.agents.benjamin_graham import BenjaminGrahamAgent
from vnpy_ai.agents.bill_ackman import BillAckmanAgent
from vnpy_ai.agents.cathie_wood import CathieWoodAgent
from vnpy_ai.agents.charlie_munger import CharlieMungerAgent
from vnpy_ai.agents.fundamentals import FundamentalsAnalystAgent
from vnpy_ai.agents.growth_agent import GrowthAnalystAgent
from vnpy_ai.agents.michael_burry import MichaelBurryAgent
from vnpy_ai.agents.mohnish_pabrai import MohnishPabraiAgent
from vnpy_ai.agents.nassim_taleb import NassimTalebAgent
from vnpy_ai.agents.news_sentiment import NewsSentimentAnalystAgent
from vnpy_ai.agents.peter_lynch import PeterLynchAgent
from vnpy_ai.agents.phil_fisher import PhilFisherAgent
from vnpy_ai.agents.rakesh_jhunjhunwala import RakeshJhunjhunwalaAgent
from vnpy_ai.agents.sentiment import SentimentAnalystAgent
from vnpy_ai.agents.stanley_druckenmiller import StanleyDruckenmillerAgent
from vnpy_ai.agents.technicals import TechnicalAnalystAgent
from vnpy_ai.agents.valuation import ValuationAnalystAgent
from vnpy_ai.agents.warren_buffett import WarrenBuffettAgent

# Single source of truth for analyst metadata.
# `agent_func` holds the agent *class* (not a function); callers instantiate
# it with a DataAdapter before invoking `.analyze(state)`.
ANALYST_CONFIG: dict[str, dict[str, Any]] = {
    "aswath_damodaran": {
        "display_name": "Aswath Damodaran",
        "description": "The Dean of Valuation",
        "investing_style": "Focuses on intrinsic value and financial metrics to assess investment opportunities through rigorous valuation analysis.",
        "agent_func": AswathDamodaranAgent,
        "type": "analyst",
        "order": 0,
    },
    "ben_graham": {
        "display_name": "Ben Graham",
        "description": "The Father of Value Investing",
        "investing_style": "Emphasizes a margin of safety and invests in undervalued companies with strong fundamentals through systematic value analysis.",
        "agent_func": BenjaminGrahamAgent,
        "type": "analyst",
        "order": 1,
    },
    "bill_ackman": {
        "display_name": "Bill Ackman",
        "description": "The Activist Investor",
        "investing_style": "Seeks to influence management and unlock value through strategic activism and contrarian investment positions.",
        "agent_func": BillAckmanAgent,
        "type": "analyst",
        "order": 2,
    },
    "cathie_wood": {
        "display_name": "Cathie Wood",
        "description": "The Queen of Growth Investing",
        "investing_style": "Focuses on disruptive innovation and growth, investing in companies that are leading technological advancements and market disruption.",
        "agent_func": CathieWoodAgent,
        "type": "analyst",
        "order": 3,
    },
    "charlie_munger": {
        "display_name": "Charlie Munger",
        "description": "The Rational Thinker",
        "investing_style": "Advocates for value investing with a focus on quality businesses and long-term growth through rational decision-making.",
        "agent_func": CharlieMungerAgent,
        "type": "analyst",
        "order": 4,
    },
    "michael_burry": {
        "display_name": "Michael Burry",
        "description": "The Big Short Contrarian",
        "investing_style": "Makes contrarian bets, often shorting overvalued markets and investing in undervalued assets through deep fundamental analysis.",
        "agent_func": MichaelBurryAgent,
        "type": "analyst",
        "order": 5,
    },
    "mohnish_pabrai": {
        "display_name": "Mohnish Pabrai",
        "description": "The Dhandho Investor",
        "investing_style": "Focuses on value investing and long-term growth through fundamental analysis and a margin of safety.",
        "agent_func": MohnishPabraiAgent,
        "type": "analyst",
        "order": 6,
    },
    "nassim_taleb": {
        "display_name": "Nassim Taleb",
        "description": "The Black Swan Risk Analyst",
        "investing_style": "Focuses on tail risk, antifragility, and asymmetric payoffs. Uses barbell strategy, avoids fragile companies via negativa, and seeks convex positions with limited downside and unlimited upside.",
        "agent_func": NassimTalebAgent,
        "type": "analyst",
        "order": 7,
    },
    "peter_lynch": {
        "display_name": "Peter Lynch",
        "description": "The 10-Bagger Investor",
        "investing_style": "Invests in companies with understandable business models and strong growth potential using the 'buy what you know' strategy.",
        "agent_func": PeterLynchAgent,
        "type": "analyst",
        "order": 8,
    },
    "phil_fisher": {
        "display_name": "Phil Fisher",
        "description": "The Scuttlebutt Investor",
        "investing_style": "Emphasizes investing in companies with strong management and innovative products, focusing on long-term growth through scuttlebutt research.",
        "agent_func": PhilFisherAgent,
        "type": "analyst",
        "order": 9,
    },
    "rakesh_jhunjhunwala": {
        "display_name": "Rakesh Jhunjhunwala",
        "description": "The Big Bull Of India",
        "investing_style": "Leverages macroeconomic insights to invest in high-growth sectors, particularly within emerging markets and domestic opportunities.",
        "agent_func": RakeshJhunjhunwalaAgent,
        "type": "analyst",
        "order": 10,
    },
    "stanley_druckenmiller": {
        "display_name": "Stanley Druckenmiller",
        "description": "The Macro Investor",
        "investing_style": "Focuses on macroeconomic trends, making large bets on currencies, commodities, and interest rates through top-down analysis.",
        "agent_func": StanleyDruckenmillerAgent,
        "type": "analyst",
        "order": 11,
    },
    "warren_buffett": {
        "display_name": "Warren Buffett",
        "description": "The Oracle of Omaha",
        "investing_style": "Seeks companies with strong fundamentals and competitive advantages through value investing and long-term ownership.",
        "agent_func": WarrenBuffettAgent,
        "type": "analyst",
        "order": 12,
    },
    "technical_analyst": {
        "display_name": "Technical Analyst",
        "description": "Chart Pattern Specialist",
        "investing_style": "Focuses on chart patterns and market trends to make investment decisions, often using technical indicators and price action analysis.",
        "agent_func": TechnicalAnalystAgent,
        "type": "analyst",
        "order": 13,
    },
    "fundamentals_analyst": {
        "display_name": "Fundamentals Analyst",
        "description": "Financial Statement Specialist",
        "investing_style": "Delves into financial statements and economic indicators to assess the intrinsic value of companies through fundamental analysis.",
        "agent_func": FundamentalsAnalystAgent,
        "type": "analyst",
        "order": 14,
    },
    "growth_analyst": {
        "display_name": "Growth Analyst",
        "description": "Growth Specialist",
        "investing_style": "Analyzes growth trends and valuation to identify growth opportunities through growth analysis.",
        "agent_func": GrowthAnalystAgent,
        "type": "analyst",
        "order": 15,
    },
    "news_sentiment_analyst": {
        "display_name": "News Sentiment Analyst",
        "description": "News Sentiment Specialist",
        "investing_style": "Analyzes news sentiment to predict market movements and identify opportunities through news analysis.",
        "agent_func": NewsSentimentAnalystAgent,
        "type": "analyst",
        "order": 16,
    },
    "sentiment_analyst": {
        "display_name": "Sentiment Analyst",
        "description": "Market Sentiment Specialist",
        "investing_style": "Gauges market sentiment and investor behavior to predict market movements and identify opportunities through behavioral analysis.",
        "agent_func": SentimentAnalystAgent,
        "type": "analyst",
        "order": 17,
    },
    "valuation_analyst": {
        "display_name": "Valuation Analyst",
        "description": "Company Valuation Specialist",
        "investing_style": "Specializes in determining the fair value of companies, using various valuation models and financial metrics for investment decisions.",
        "agent_func": ValuationAnalystAgent,
        "type": "analyst",
        "order": 18,
    },
}

# Backwards-compatible ordered list of (display_name, key) tuples.
ANALYST_ORDER = [
    (config["display_name"], key)
    for key, config in sorted(ANALYST_CONFIG.items(), key=lambda x: x[1]["order"])
]


def get_analyst_nodes() -> dict[str, tuple[str, Any]]:
    """Map analyst keys to (node_name, agent_class) tuples.

    Note: unlike upstream, `agent_func` here is a *class* that must be
    instantiated with a DataAdapter before calling `.analyze(state)`.
    """
    return {
        key: (f"{key}_agent", config["agent_func"])
        for key, config in ANALYST_CONFIG.items()
    }


def get_agents_list() -> list[dict[str, Any]]:
    """Return analyst metadata ordered by `order` for API/UI consumers."""
    return [
        {
            "key": key,
            "display_name": config["display_name"],
            "description": config["description"],
            "investing_style": config["investing_style"],
            "order": config["order"],
        }
        for key, config in sorted(
            ANALYST_CONFIG.items(), key=lambda x: x[1]["order"]
        )
    ]
