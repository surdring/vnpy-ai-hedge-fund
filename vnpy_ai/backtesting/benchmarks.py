class Benchmark:
    def __init__(self, symbol: str = "SPY"):
        self.symbol = symbol
        self.returns: list[float] = []

    def compare(self, strategy_returns: list[float]) -> dict:
        return {
            "strategy_return": sum(strategy_returns),
            "benchmark_return": sum(self.returns),
            "alpha": sum(strategy_returns) - sum(self.returns),
        }
