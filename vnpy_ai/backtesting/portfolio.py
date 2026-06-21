class Portfolio:
    def __init__(self, initial_capital: float = 100000.0):
        self.cash = initial_capital
        self.positions: dict[str, int] = {}
        self.equity_history: list[float] = [initial_capital]

    def update(self, ticker: str, quantity: int, price: float, is_buy: bool):
        if is_buy:
            self.positions[ticker] = self.positions.get(ticker, 0) + quantity
            self.cash -= quantity * price
        else:
            self.positions[ticker] = self.positions.get(ticker, 0) - quantity
            self.cash += quantity * price

    def get_total_equity(self, prices: dict[str, float]) -> float:
        positions_value = sum(qty * prices.get(t, 0) for t, qty in self.positions.items())
        return self.cash + positions_value
