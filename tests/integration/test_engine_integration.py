from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine

from vnpy_ai.app import AiHedgeFundApp
from vnpy_ai.engine import AiHedgeFundEngine


def test_main_engine_add_app_loads_ai_engine() -> None:
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    engine = main_engine.add_app(AiHedgeFundApp)
    try:
        assert isinstance(engine, AiHedgeFundEngine)
        assert engine.get_status().enabled is False
    finally:
        main_engine.close()

