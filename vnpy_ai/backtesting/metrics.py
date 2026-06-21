import numpy as np


class PerformanceMetrics:
    @staticmethod
    def sharpe_ratio(returns: list[float], risk_free_rate: float = 0.02) -> float:
        if not returns:
            return 0.0
        arr = np.array(returns)
        return float((arr.mean() - risk_free_rate / 252) / (arr.std() + 1e-10) * np.sqrt(252))

    @staticmethod
    def sortino_ratio(returns: list[float], risk_free_rate: float = 0.02) -> float:
        if not returns:
            return 0.0
        arr = np.array(returns)
        downside = arr[arr < 0]
        return float((arr.mean() - risk_free_rate / 252) / (downside.std() + 1e-10) * np.sqrt(252))

    @staticmethod
    def max_drawdown(equity_curve: list[float]) -> float:
        if not equity_curve:
            return 0.0
        peak = np.maximum.accumulate(equity_curve)
        drawdown = (np.array(equity_curve) - peak) / peak
        return float(abs(drawdown.min()))

    @staticmethod
    def annualized_return(equity_curve: list[float], days: int = 252) -> float:
        if len(equity_curve) < 2:
            return 0.0
        return float((equity_curve[-1] / equity_curve[0]) ** (252 / days) - 1)

    @staticmethod
    def win_rate(trades: list[dict]) -> float:
        if not trades:
            return 0.0
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        return wins / len(trades)
