class Valuation:
    @staticmethod
    def calculate_position_value(quantity: int, price: float) -> float:
        return float(quantity * price)

    @staticmethod
    def calculate_total_value(positions: dict, prices: dict, cash: float) -> float:
        return float(cash + sum(qty * prices.get(t, 0) for t, qty in positions.items()))
