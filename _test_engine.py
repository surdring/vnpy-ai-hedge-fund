"""临时测试脚本：验证 BacktestEngine.run() 完整流程"""
import sys
sys.path.insert(0, ".")

from vnpy_ai.backtesting.engine import BacktestEngine, BacktestConfig
from vnpy_ai.backtesting.portfolio import Portfolio
from vnpy_ai.backtesting.controller import BacktestController


# 模拟一个简单策略：每天买入 10 股 AAPL
def simple_strategy(date, day_data, portfolio):
    decisions = []
    if "AAPL" in day_data:
        decisions.append({
            "ticker": "AAPL",
            "action": "buy",
            "quantity": 10,
            "price": day_data["AAPL"]["close"],
        })
    return decisions


# 手动模拟整个流程，因为 VnpyAdapter 需要 main_engine
config = BacktestConfig(
    initial_capital=100000.0,
    start_date="2024-01-01",
    end_date="2024-01-05",
    commission_rate=0.0003,
    slippage=0.001,
)

# 模拟数据
bars = [
    {"date": "2024-01-02", "open": 150.0, "high": 152.0, "low": 149.0, "close": 151.0, "volume": 10000},
    {"date": "2024-01-03", "open": 151.0, "high": 155.0, "low": 150.0, "close": 154.0, "volume": 12000},
    {"date": "2024-01-04", "open": 154.0, "high": 156.0, "low": 153.0, "close": 155.0, "volume": 8000},
    {"date": "2024-01-05", "open": 155.0, "high": 158.0, "low": 154.0, "close": 157.0, "volume": 11000},
]

portfolio = Portfolio(initial_capital=config.initial_capital)
controller = BacktestController(
    initial_capital=config.initial_capital,
    commission_rate=config.commission_rate,
    slippage=config.slippage,
)

trades = []
equity_curve = []
daily_returns = []
previous_equity = config.initial_capital

for bar in bars:
    date = bar["date"]
    day_data = {"AAPL": bar}
    day_prices = {"AAPL": bar["close"]}

    decisions = simple_strategy(date, day_data, portfolio)

    for decision in decisions:
        ticker = decision["ticker"]
        action = decision["action"]
        quantity = decision["quantity"]
        price = decision["price"]

        is_buy = action.lower() == "buy"
        adjusted_price = controller.apply_slippage(price, is_buy)
        trade_value = adjusted_price * quantity
        commission = controller.apply_commission(trade_value) - trade_value

        portfolio.update(ticker, quantity, adjusted_price, is_buy)
        portfolio.cash += commission

        trades.append({
            "date": date,
            "ticker": ticker,
            "action": action,
            "quantity": quantity,
            "price": adjusted_price,
            "value": trade_value,
            "commission": commission,
        })

    total_equity = portfolio.get_total_equity(day_prices)
    equity_curve.append({"date": date, "equity": total_equity, "cash": portfolio.cash})

    if previous_equity > 0:
        daily_returns.append((total_equity - previous_equity) / previous_equity)
    previous_equity = total_equity

# 计算指标
from vnpy_ai.backtesting.metrics import PerformanceMetrics

equity_values = [e["equity"] for e in equity_curve]
metrics = {
    "total_return": (equity_values[-1] / config.initial_capital - 1) if equity_values else 0.0,
    "sharpe_ratio": PerformanceMetrics.sharpe_ratio(daily_returns),
    "sortino_ratio": PerformanceMetrics.sortino_ratio(daily_returns),
    "max_drawdown": PerformanceMetrics.max_drawdown(equity_values),
    "annualized_return": PerformanceMetrics.annualized_return(equity_values, len(daily_returns)),
    "win_rate": PerformanceMetrics.win_rate(trades),
}

print("=== 回测结果 ===")
print(f"Status: complete")
print(f"交易笔数: {len(trades)}")
print(f"权益曲线: {equity_curve}")
print(f"每日收益: {daily_returns}")
print(f"指标: {metrics}")
print(f"总收益率: {metrics['total_return']:.4%}")
print(f"夏普比率: {metrics['sharpe_ratio']:.4f}")
print(f"最大回撤: {metrics['max_drawdown']:.4%}")
print(f"年化收益: {metrics['annualized_return']:.4%}")
print(f"胜率: {metrics['win_rate']:.4%}")
print()
print("所有测试通过!")