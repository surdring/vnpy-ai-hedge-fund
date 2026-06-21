from datetime import datetime

from vnpy.trader.constant import Exchange
from vnpy.trader.object import BarData

from vnpy_ai.data_adapter import bar_to_price, parse_vt_symbol


def test_parse_vt_symbol_with_exchange() -> None:
    symbol, exchange = parse_vt_symbol("AAPL.NASDAQ")
    assert symbol == "AAPL"
    assert exchange == Exchange.NASDAQ


def test_bar_to_price() -> None:
    bar = BarData(
        symbol="AAPL",
        exchange=Exchange.NASDAQ,
        datetime=datetime(2024, 3, 1),
        open_price=1,
        high_price=3,
        low_price=0.5,
        close_price=2,
        volume=100,
        gateway_name="test",
    )
    price = bar_to_price(bar)
    assert price.open == 1
    assert price.close == 2
    assert price.volume == 100
    assert price.time == "2024-03-01"

