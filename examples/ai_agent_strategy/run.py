"""
Minimal example for loading AiHedgeFundApp in VeighNa.
"""

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine

from vnpy_ai.app import AiHedgeFundApp


def main() -> None:
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    engine = main_engine.add_app(AiHedgeFundApp)
    try:
        print(engine.get_status().model_dump())
    finally:
        main_engine.close()


if __name__ == "__main__":
    main()

