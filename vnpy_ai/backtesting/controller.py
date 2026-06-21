class BacktestController:
    def __init__(self, initial_capital: float = 100000.0, commission_rate: float = 0.0003, slippage: float = 0.001):
        self.capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage

    def apply_commission(self, value: float) -> float:
        return value * (1 - self.commission_rate)

    def apply_slippage(self, price: float, is_buy: bool = True) -> float:
        return price * (1 + self.slippage) if is_buy else price * (1 - self.slippage)
