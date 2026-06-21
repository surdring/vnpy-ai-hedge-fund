class BacktestTrader:
    def __init__(self, controller):
        self.controller = controller
        self.orders: list = []

    def execute_order(self, ticker: str, action: str, quantity: int, price: float) -> dict:
        order = {"ticker": ticker, "action": action, "quantity": quantity, "price": price, "status": "filled"}
        self.orders.append(order)
        return order
