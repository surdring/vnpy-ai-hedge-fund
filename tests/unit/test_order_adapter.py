from vnpy.trader.constant import Direction, Offset

from vnpy_ai.models import PortfolioDecision
from vnpy_ai.order_adapter import OrderAdapter


def test_hold_decision_returns_no_order() -> None:
    adapter = OrderAdapter()
    assert adapter.decision_to_order(PortfolioDecision(ticker="AAPL.NASDAQ")) is None


def test_buy_decision_maps_to_long_open() -> None:
    adapter = OrderAdapter()
    order = adapter.decision_to_order(
        PortfolioDecision(ticker="AAPL.NASDAQ", action="buy", quantity=10, price=100)
    )
    assert order is not None
    assert order.symbol == "AAPL"
    assert order.direction == Direction.LONG
    assert order.offset == Offset.OPEN
    assert order.volume == 10


def test_invalid_quantity_rejected() -> None:
    adapter = OrderAdapter()
    result = adapter.validate_decision(
        PortfolioDecision(ticker="AAPL.NASDAQ", action="sell", quantity=0)
    )
    assert not result.ok

