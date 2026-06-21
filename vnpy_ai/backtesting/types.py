from pydantic import BaseModel


class BacktestRequest(BaseModel):
    tickers: list[str] = ["AAPL"]
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    initial_capital: float = 100000.0


class BacktestResult(BaseModel):
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    trades: list[dict] = []
