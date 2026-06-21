"""
Risk Manager Agent — volatility-adjusted position sizing and risk control.

Original upstream: ai-hedge-fund/src/agents/risk_manager.py
Copyright (c) Virat Singh, MIT License.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
import pandas as pd

from .base import AgentBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------


def prices_to_df(prices: list[Any]) -> pd.DataFrame:
    """Convert a list of Price objects (or dicts) into a DataFrame with a 'close' column.

    Returns an empty DataFrame if the input is empty.
    """
    if not prices:
        return pd.DataFrame()

    records: list[dict[str, Any]] = []
    for p in prices:
        if hasattr(p, "model_dump"):
            records.append(p.model_dump())
        elif isinstance(p, dict):
            records.append(p)
        else:
            records.append({"close": float(p)})

    df = pd.DataFrame(records)
    if "time" in df.columns:
        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values("time")
    return df


def calculate_volatility_metrics(
    prices_df: pd.DataFrame, lookback_days: int = 60
) -> dict[str, Any]:
    """Calculate comprehensive volatility metrics from price data.

    Args:
        prices_df: DataFrame with a 'close' column.
        lookback_days: Number of most recent days used for volatility calculation.

    Returns:
        Dict with daily_volatility, annualized_volatility, volatility_percentile,
        and data_points.
    """
    if len(prices_df) < 2:
        return {
            "daily_volatility": 0.05,
            "annualized_volatility": 0.05 * np.sqrt(252),
            "volatility_percentile": 100,
            "data_points": len(prices_df),
        }

    daily_returns = prices_df["close"].pct_change().dropna()

    if len(daily_returns) < 2:
        return {
            "daily_volatility": 0.05,
            "annualized_volatility": 0.05 * np.sqrt(252),
            "volatility_percentile": 100,
            "data_points": len(daily_returns),
        }

    recent_returns = daily_returns.tail(min(lookback_days, len(daily_returns)))
    daily_vol = recent_returns.std()
    annualized_vol = daily_vol * np.sqrt(252)

    # Percentile rank of current volatility vs historical rolling volatility
    if len(daily_returns) >= 30:
        rolling_vol = daily_returns.rolling(window=30).std().dropna()
        if len(rolling_vol) > 0:
            current_vol_percentile = (rolling_vol <= daily_vol).mean() * 100
        else:
            current_vol_percentile = 50.0
    else:
        current_vol_percentile = 50.0

    return {
        "daily_volatility": float(daily_vol) if not np.isnan(daily_vol) else 0.025,
        "annualized_volatility": float(annualized_vol) if not np.isnan(annualized_vol) else 0.25,
        "volatility_percentile": float(current_vol_percentile) if not np.isnan(current_vol_percentile) else 50.0,
        "data_points": len(recent_returns),
    }


def calculate_var(
    prices_df: pd.DataFrame, confidence_level: float = 0.95
) -> dict[str, Any]:
    """Calculate parametric Value at Risk (VaR) from price data.

    Uses the parametric (variance-covariance) method assuming log-returns are
    normally distributed with zero mean.

    Args:
        prices_df: DataFrame with a 'close' column.
        confidence_level: Confidence level (default 0.95 for 95% VaR).

    Returns:
        Dict with var_95, var_99, and current_price.
    """
    if len(prices_df) < 2:
        return {"var_95": 0.0, "var_99": 0.0, "current_price": 0.0}

    daily_returns = prices_df["close"].pct_change().dropna()
    if len(daily_returns) < 2:
        return {"var_95": 0.0, "var_99": 0.0, "current_price": 0.0}

    daily_vol = daily_returns.std()
    current_price = float(prices_df["close"].iloc[-1])

    # Z-scores for common confidence levels (standard normal distribution)
    # 95% → 1.64485, 99% → 2.32635
    z_95 = 1.64485
    z_99 = 2.32635

    var_95_pct = float(z_95 * daily_vol) if not np.isnan(daily_vol) else 0.05
    var_99_pct = float(z_99 * daily_vol) if not np.isnan(daily_vol) else 0.07

    return {
        "var_95": var_95_pct,
        "var_99": var_99_pct,
        "current_price": current_price,
    }


def calculate_correlation_analysis(
    returns_by_ticker: dict[str, pd.Series],
) -> dict[str, Any]:
    """Compute correlation matrix and statistics from returns keyed by ticker.

    Args:
        returns_by_ticker: Dict mapping ticker -> pd.Series of daily returns.

    Returns:
        Dict with correlation_matrix (DataFrame or None), max_correlation,
        avg_correlation, and diversification_score.
    """
    if len(returns_by_ticker) < 2:
        return {
            "correlation_matrix": None,
            "max_correlation": 0.0,
            "avg_correlation": 0.0,
            "diversification_score": 0.5,
        }

    try:
        returns_df = pd.DataFrame(returns_by_ticker).dropna(how="any")
        if returns_df.shape[1] < 2 or returns_df.shape[0] < 5:
            return {
                "correlation_matrix": None,
                "max_correlation": 0.0,
                "avg_correlation": 0.0,
                "diversification_score": 0.5,
            }

        corr_matrix = returns_df.corr()

        # Extract upper triangle (excluding diagonal) for summary stats
        upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
        values = upper.stack().values
        if len(values) == 0:
            return {
                "correlation_matrix": corr_matrix,
                "max_correlation": 0.0,
                "avg_correlation": 0.0,
                "diversification_score": 0.5,
            }

        avg_corr = float(np.mean(np.abs(values)))
        max_corr = float(np.max(np.abs(values))) if len(values) > 0 else 0.0

        # Diversification score: 1 = perfectly diversified, 0 = highly correlated
        diversification_score = float(max(0.0, min(1.0, 1.0 - avg_corr)))

        return {
            "correlation_matrix": corr_matrix,
            "max_correlation": max_corr,
            "avg_correlation": avg_corr,
            "diversification_score": diversification_score,
        }
    except Exception:
        logger.debug("Correlation analysis failed", exc_info=True)
        return {
            "correlation_matrix": None,
            "max_correlation": 0.0,
            "avg_correlation": 0.0,
            "diversification_score": 0.5,
        }


def calculate_volatility_adjusted_limit(annualized_volatility: float) -> float:
    """Calculate position limit as percentage of portfolio based on volatility.

    Logic:
        - Low volatility (<15%): Up to 25% allocation
        - Medium volatility (15-30%): 15-20% allocation
        - High volatility (>30%): 10-15% allocation
        - Very high volatility (>50%): Max 10% allocation
    """
    base_limit = 0.20  # 20% baseline

    if annualized_volatility < 0.15:
        vol_multiplier = 1.25  # Up to 25%
    elif annualized_volatility < 0.30:
        vol_multiplier = 1.0 - (annualized_volatility - 0.15) * 0.5
    elif annualized_volatility < 0.50:
        vol_multiplier = 0.75 - (annualized_volatility - 0.30) * 0.5
    else:
        vol_multiplier = 0.50  # Max 10%

    vol_multiplier = max(0.25, min(1.25, vol_multiplier))  # 5% to 25% range
    return base_limit * vol_multiplier


def calculate_correlation_multiplier(avg_correlation: float) -> float:
    """Map average correlation to an adjustment multiplier.

    - Very high correlation (>= 0.8): reduce limit sharply (0.7x)
    - High correlation (0.6-0.8): reduce (0.85x)
    - Moderate correlation (0.4-0.6): neutral (1.0x)
    - Low correlation (0.2-0.4): slight increase (1.05x)
    - Very low correlation (< 0.2): increase (1.10x)
    """
    if avg_correlation >= 0.80:
        return 0.70
    if avg_correlation >= 0.60:
        return 0.85
    if avg_correlation >= 0.40:
        return 1.00
    if avg_correlation >= 0.20:
        return 1.05
    return 1.10


def calculate_position_limits(
    volatility_data: dict[str, dict[str, Any]],
    portfolio: dict[str, Any],
    max_portfolio_risk: float = 0.02,
) -> dict[str, float]:
    """Calculate volatility-adjusted position limits for each ticker.

    Args:
        volatility_data: Dict mapping ticker -> volatility metrics.
        portfolio: Portfolio dict with 'cash' and optional 'positions'.
        max_portfolio_risk: Maximum portfolio risk per position (default 2%).

    Returns:
        Dict mapping ticker -> max position limit (as fraction of portfolio value).
    """
    limits: dict[str, float] = {}
    for ticker, vol in volatility_data.items():
        ann_vol = vol.get("annualized_volatility", 0.25)
        vol_adjusted_limit = calculate_volatility_adjusted_limit(ann_vol)
        limits[ticker] = vol_adjusted_limit
    return limits


# ---------------------------------------------------------------------------
# RiskManagerAgent
# ---------------------------------------------------------------------------


class RiskManagerAgent(AgentBase):
    """Risk Manager: volatility-adjusted position sizing, VaR, and correlation analysis.

    This agent performs deterministic risk calculations using numpy — no LLM
    calls are involved.  It evaluates each ticker's volatility profile, computes
    Value at Risk, and recommends position limits based on volatility and
    cross-asset correlations.
    """

    agent_id = "risk_manager_agent"
    agent_name = "Risk Manager"

    # ------------------------------------------------------------------
    # analyze
    # ------------------------------------------------------------------

    def analyze(self, state: dict[str, Any]) -> dict[str, Any]:
        """Run risk analysis for all tickers in the workflow state.

        Args:
            state: Workflow state dict with keys:
                - data.tickers: list of ticker symbols
                - data.start_date / data.end_date: date range strings
                - data.portfolio (optional): portfolio dict; falls back
                  to self.get_portfolio().

        Returns:
            Dict with agent_id, agent_name, risk_assessments (per ticker),
            and portfolio_risk.
        """
        data = state.get("data", state)
        tickers: list[str] = list(data.get("tickers", []))
        start_date = data.get("start_date", "")
        end_date = data.get("end_date", "")

        # Try to get portfolio from state, fall back to adapter
        portfolio = data.get("portfolio", None)
        if portfolio is None:
            portfolio = self.get_portfolio()

        # --- 1. Fetch prices and compute per-ticker metrics ---
        current_prices: dict[str, float] = {}
        volatility_data: dict[str, dict[str, Any]] = {}
        var_data: dict[str, dict[str, Any]] = {}
        returns_by_ticker: dict[str, pd.Series] = {}

        for ticker in tickers:
            prices = self.get_prices(ticker, start_date, end_date)

            if not prices:
                logger.debug("RiskManager: no price data for %s, using defaults", ticker)
                self._set_defaults(ticker, current_prices, volatility_data, var_data)
                continue

            prices_df = prices_to_df(prices)
            if prices_df.empty or len(prices_df) < 2:
                logger.debug("RiskManager: insufficient price data for %s", ticker)
                self._set_defaults(ticker, current_prices, volatility_data, var_data)
                continue

            current_price = float(prices_df["close"].iloc[-1])
            current_prices[ticker] = current_price

            volatility_data[ticker] = calculate_volatility_metrics(prices_df)
            var_data[ticker] = calculate_var(prices_df)

            daily_returns = prices_df["close"].pct_change().dropna()
            if len(daily_returns) > 0:
                returns_by_ticker[ticker] = daily_returns

        # --- 2. Correlation analysis across all tickers ---
        corr_result = calculate_correlation_analysis(returns_by_ticker)
        correlation_matrix = corr_result.get("correlation_matrix")

        # --- 3. Compute portfolio-level metrics ---
        total_portfolio_value = self._compute_portfolio_value(portfolio, current_prices)

        # --- 4. Per-ticker risk assessments ---
        risk_assessments: dict[str, dict[str, Any]] = {}

        for ticker in tickers:
            if ticker not in current_prices or current_prices[ticker] <= 0:
                risk_assessments[ticker] = {
                    "daily_volatility": 0.05,
                    "annualized_volatility": 0.05 * np.sqrt(252),
                    "volatility_percentile": 100.0,
                    "var_95": 0.05,
                    "current_price": 0.0,
                    "max_position_limit": 0.0,
                    "remaining_position_limit": 0.0,
                }
                continue

            vol = volatility_data.get(ticker, {})
            var_d = var_data.get(ticker, {})

            # Volatility-adjusted limit
            vol_limit_pct = calculate_volatility_adjusted_limit(
                vol.get("annualized_volatility", 0.25)
            )

            # Correlation adjustment
            corr_multiplier = 1.0
            if correlation_matrix is not None and ticker in correlation_matrix.columns:
                comparable = [
                    t for t in correlation_matrix.columns if t != ticker
                ]
                if comparable:
                    series = correlation_matrix.loc[ticker, comparable].dropna()
                    if len(series) > 0:
                        avg_corr = float(series.mean())
                        corr_multiplier = calculate_correlation_multiplier(avg_corr)

            combined_limit_pct = vol_limit_pct * corr_multiplier
            position_limit = total_portfolio_value * combined_limit_pct

            # Current position value
            current_position_value = self._get_position_value(
                portfolio, ticker, current_prices[ticker]
            )
            remaining_limit = position_limit - current_position_value
            max_position_size = min(remaining_limit, portfolio.get("cash", 0))

            risk_assessments[ticker] = {
                "daily_volatility": float(vol.get("daily_volatility", 0.05)),
                "annualized_volatility": float(vol.get("annualized_volatility", 0.25)),
                "volatility_percentile": float(vol.get("volatility_percentile", 100.0)),
                "var_95": float(var_d.get("var_95", 0.05)),
                "current_price": float(current_prices[ticker]),
                "max_position_limit": float(combined_limit_pct),
                "remaining_position_limit": float(max_position_size),
            }

        # --- 5. Portfolio-level risk summary ---
        total_var = self._compute_total_var(
            var_data, current_prices, portfolio, total_portfolio_value
        )

        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "risk_assessments": risk_assessments,
            "portfolio_risk": {
                "total_var": total_var,
                "max_correlation": float(corr_result.get("max_correlation", 0.0)),
                "diversification_score": float(corr_result.get("diversification_score", 0.5)),
            },
        }

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------

    @staticmethod
    def _set_defaults(
        ticker: str,
        current_prices: dict[str, float],
        volatility_data: dict[str, dict[str, Any]],
        var_data: dict[str, dict[str, Any]],
    ) -> None:
        """Fill fallback values when price data is unavailable."""
        current_prices[ticker] = 0.0
        volatility_data[ticker] = {
            "daily_volatility": 0.05,
            "annualized_volatility": 0.05 * np.sqrt(252),
            "volatility_percentile": 100.0,
            "data_points": 0,
        }
        var_data[ticker] = {
            "var_95": 0.05,
            "var_99": 0.07,
            "current_price": 0.0,
        }

    @staticmethod
    def _compute_portfolio_value(
        portfolio: dict[str, Any],
        current_prices: dict[str, float],
    ) -> float:
        """Compute total portfolio value (cash + market value of positions)."""
        total = float(portfolio.get("cash", 0.0))

        positions = portfolio.get("positions", {})
        if isinstance(positions, dict):
            # Upstream format: {ticker: {"long": N, "short": M}}
            for ticker, pos in positions.items():
                if ticker in current_prices:
                    price = current_prices[ticker]
                    total += pos.get("long", 0) * price
                    total -= pos.get("short", 0) * price
        elif isinstance(positions, list):
            # DataAdapter format: [{"ticker": ..., "quantity": ..., "market_value": ...}]
            for pos in positions:
                ticker = pos.get("ticker", "")
                if ticker in current_prices and current_prices[ticker] > 0:
                    total += pos.get("market_value", 0.0)
                elif ticker in current_prices:
                    quantity = float(pos.get("quantity", 0))
                    total += quantity * current_prices.get(ticker, 0.0)

        return max(total, 0.0)

    @staticmethod
    def _get_position_value(
        portfolio: dict[str, Any],
        ticker: str,
        current_price: float,
    ) -> float:
        """Return the absolute market value of the current position for a ticker."""
        positions = portfolio.get("positions", {})
        if isinstance(positions, dict):
            pos = positions.get(ticker, {})
            long_val = pos.get("long", 0) * current_price
            short_val = pos.get("short", 0) * current_price
            return float(abs(long_val - short_val))
        elif isinstance(positions, list):
            for pos in positions:
                if pos.get("ticker") == ticker:
                    mv = pos.get("market_value", 0.0)
                    if mv:
                        return abs(float(mv))
                    quantity = float(pos.get("quantity", 0))
                    return abs(quantity * current_price)
        return 0.0

    @staticmethod
    def _compute_total_var(
        var_data: dict[str, dict[str, Any]],
        current_prices: dict[str, float],
        portfolio: dict[str, Any],
        total_portfolio_value: float,
    ) -> float:
        """Compute approximate portfolio-level VaR as weighted average.

        Falls back to a simple average when weights cannot be determined.
        """
        if total_portfolio_value <= 0 or not var_data:
            return 0.0

        weighted_var = 0.0
        total_weight = 0.0

        for ticker, var_d in var_data.items():
            price = current_prices.get(ticker, 0.0)
            if price <= 0:
                continue
            position_value = RiskManagerAgent._get_position_value(
                portfolio, ticker, price
            )
            weight = position_value / total_portfolio_value if position_value > 0 else 0.0
            if weight == 0.0:
                # Use equal weight for tickers with no position
                weight = 1.0 / max(len(var_data), 1)
            weighted_var += var_d.get("var_95", 0.05) * weight
            total_weight += weight

        if total_weight > 0:
            return float(weighted_var / total_weight)
        return 0.0