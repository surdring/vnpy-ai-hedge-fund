"""
Console display utilities for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/display.py (MIT License, Virat Singh).
Simplified to avoid the optional `colorama`/`tabulate` dependencies; output
is plain text via `print()`. The public API stays compatible with upstream
callers (`print_trading_output`, `print_backtest_results`, `format_backtest_row`).
"""

from __future__ import annotations

import json
import os
from typing import Any

from vnpy_ai.utils.analysts import ANALYST_ORDER


def sort_agent_signals(signals: list[list[Any]]) -> list[list[Any]]:
    """Sort agent signals in a consistent order based on ANALYST_ORDER."""
    analyst_order = {display: idx for idx, (display, _) in enumerate(ANALYST_ORDER)}
    analyst_order["Risk Management"] = len(ANALYST_ORDER)
    return sorted(signals, key=lambda x: analyst_order.get(x[0], 999))


def _wrap_text(text: str, max_line_length: int = 60) -> str:
    """Wrap long text to a fixed line length for readable console output."""
    if not text:
        return ""
    lines: list[str] = []
    current_line = ""
    for word in text.split():
        if len(current_line) + len(word) + 1 > max_line_length:
            if current_line:
                lines.append(current_line)
            current_line = word
        else:
            current_line = f"{current_line} {word}" if current_line else word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)


def _stringify_reasoning(reasoning: Any) -> str:
    """Normalize reasoning values (str/dict/other) to a string."""
    if isinstance(reasoning, str):
        return reasoning
    if isinstance(reasoning, dict):
        return json.dumps(reasoning, indent=2, ensure_ascii=False)
    return str(reasoning)


def print_trading_output(result: dict[str, Any]) -> None:
    """Print formatted trading results for multiple tickers.

    Args:
        result: Dict containing 'decisions' and 'analyst_signals'.
    """
    decisions = result.get("decisions")
    if not decisions:
        print("No trading decisions available")
        return

    for ticker, decision in decisions.items():
        print(f"\nAnalysis for {ticker}")
        print("=" * 50)

        table_data: list[list[str]] = []
        for agent, signals in result.get("analyst_signals", {}).items():
            if ticker not in signals:
                continue
            if agent == "risk_management_agent":
                continue
            signal = signals[ticker]
            agent_name = agent.replace("_agent", "").replace("_", " ").title()
            signal_type = signal.get("signal", "").upper()
            confidence = signal.get("confidence", 0)
            reasoning_str = _wrap_text(
                _stringify_reasoning(signal.get("reasoning", ""))
            )
            table_data.append(
                [agent_name, signal_type, f"{confidence}%", reasoning_str]
            )

        table_data = sort_agent_signals(table_data)

        print(f"\nAGENT ANALYSIS: [{ticker}]")
        print(f"{'Agent':<24}{'Signal':<10}{'Confidence':<12}Reasoning")
        print("-" * 80)
        for row in table_data:
            print(f"{row[0]:<24}{row[1]:<10}{row[2]:<12}{row[3]}")

        action = decision.get("action", "").upper()
        reasoning = _wrap_text(_stringify_reasoning(decision.get("reasoning", "")))
        print(f"\nTRADING DECISION: [{ticker}]")
        print(f"  Action     : {action}")
        print(f"  Quantity   : {decision.get('quantity')}")
        print(f"  Confidence : {decision.get('confidence', 0):.1f}%")
        print(f"  Reasoning  : {reasoning}")

    print("\nPORTFOLIO SUMMARY:")
    analyst_signals = result.get("analyst_signals", {})
    print(
        f"{'Ticker':<10}{'Action':<8}{'Quantity':<10}{'Confidence':<12}"
        f"{'Bullish':<9}{'Bearish':<9}{'Neutral':<9}"
    )
    print("-" * 67)
    for ticker, decision in decisions.items():
        action = decision.get("action", "").upper()
        bullish_count = bearish_count = neutral_count = 0
        if analyst_signals:
            for signals in analyst_signals.values():
                if ticker in signals:
                    signal = signals[ticker].get("signal", "").upper()
                    if signal == "BULLISH":
                        bullish_count += 1
                    elif signal == "BEARISH":
                        bearish_count += 1
                    elif signal == "NEUTRAL":
                        neutral_count += 1
        print(
            f"{ticker:<10}{action:<8}{decision.get('quantity', 0)!s:<10}"
            f"{decision.get('confidence', 0):.1f}%{'':<6}"
            f"{bullish_count:<9}{bearish_count:<9}{neutral_count:<9}"
        )

    # Print portfolio manager reasoning (common for all tickers).
    portfolio_manager_reasoning = next(
        (d.get("reasoning") for d in decisions.values() if d.get("reasoning")),
        None,
    )
    if portfolio_manager_reasoning:
        wrapped = _wrap_text(_stringify_reasoning(portfolio_manager_reasoning))
        print(f"\nPortfolio Strategy:\n{wrapped}")


def print_backtest_results(table_rows: list[list[Any]]) -> None:
    """Print backtest results in a plain-text table.

    Args:
        table_rows: List of row lists produced by `format_backtest_row`.
    """
    os.system("cls" if os.name == "nt" else "clear")

    ticker_rows: list[list[Any]] = []
    summary_rows: list[list[Any]] = []
    for row in table_rows:
        if isinstance(row[1], str) and "PORTFOLIO SUMMARY" in row[1]:
            summary_rows.append(row)
        else:
            ticker_rows.append(row)

    if summary_rows:
        latest_summary = max(summary_rows, key=lambda r: r[0])
        print("\nPORTFOLIO SUMMARY:")
        # Summary rows carry numeric values in fixed positions; guard with
        # defensive checks since the simplified format may differ.
        if len(latest_summary) > 10:
            print(f"Return: {latest_summary[10]}")
        if len(latest_summary) > 11 and latest_summary[11]:
            print(f"Sharpe Ratio: {latest_summary[11]}")
        if len(latest_summary) > 12 and latest_summary[12]:
            print(f"Sortino Ratio: {latest_summary[12]}")
        if len(latest_summary) > 13 and latest_summary[13]:
            print(f"Max Drawdown: {latest_summary[13]}")

    print("\n" * 2)
    headers = [
        "Date",
        "Ticker",
        "Action",
        "Quantity",
        "Price",
        "Long Shares",
        "Short Shares",
        "Position Value",
    ]
    print("  ".join(f"{h:<14}" for h in headers))
    print("-" * (14 * len(headers) + 2 * (len(headers) - 1)))
    for row in ticker_rows:
        print("  ".join(f"{str(c):<14}" for c in row[: len(headers)]))

    print("\n" * 4)


def format_backtest_row(
    date: str,
    ticker: str,
    action: str,
    quantity: float,
    price: float,
    long_shares: float = 0,
    short_shares: float = 0,
    position_value: float = 0,
    is_summary: bool = False,
    total_value: float | None = None,
    return_pct: float | None = None,
    cash_balance: float | None = None,
    total_position_value: float | None = None,
    sharpe_ratio: float | None = None,
    sortino_ratio: float | None = None,
    max_drawdown: float | None = None,
    benchmark_return_pct: float | None = None,
) -> list[Any]:
    """Format a row for the backtest results table.

    The returned list mirrors upstream column layout so callers can switch
    between the rich-based and simplified renderers without changes.
    """
    if is_summary:
        return [
            date,
            "PORTFOLIO SUMMARY",
            "",
            "",
            "",
            "",
            "",
            f"${total_position_value:,.2f}" if total_position_value is not None else "",
            f"${cash_balance:,.2f}" if cash_balance is not None else "",
            f"${total_value:,.2f}" if total_value is not None else "",
            f"{return_pct:+.2f}%" if return_pct is not None else "",
            f"{sharpe_ratio:.2f}" if sharpe_ratio is not None else "",
            f"{sortino_ratio:.2f}" if sortino_ratio is not None else "",
            f"{max_drawdown:.2f}%" if max_drawdown is not None else "",
            f"{benchmark_return_pct:+.2f}%" if benchmark_return_pct is not None else "",
        ]

    return [
        date,
        ticker,
        action.upper(),
        f"{quantity:,.0f}",
        f"{price:,.2f}",
        f"{long_shares:,.0f}",
        f"{short_shares:,.0f}",
        f"${position_value:,.2f}",
    ]
