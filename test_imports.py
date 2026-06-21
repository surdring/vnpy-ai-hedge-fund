"""Full test: imports + widget creation (run with python -E)"""
import sys
import pathlib

sys.path.insert(0, "d:\\develop\\vnpy-ai-hedge-fund\\vnpy\\examples\\veighna_trader")

# Patch pathlib (safety net for Trae sandbox)
_o = pathlib.Path.__new__
def _p(c, *a, **k):
    return _o(c, *("" if x is None else x for x in a), **k)
pathlib.Path.__new__ = _p
print("pathlib patched OK")

# Test all imports
from vnpy.event import EventEngine
print("EventEngine OK")
from vnpy.trader.engine import MainEngine
print("MainEngine OK")
from vnpy.trader.ui import MainWindow, create_qapp
print("MainWindow OK")
from vnpy_ai.app import AiHedgeFundApp
print("AiHedgeFundApp OK")
from vnpy_ai.ui import AiHedgeFundWidget
print("AiHedgeFundWidget OK")
from PySide6.QtWidgets import QApplication
_qapp = QApplication.instance() or QApplication(sys.argv)
print("QApplication OK")

# Test the MainWindow widget creation path
app = AiHedgeFundApp()
print(f"  app_module={app.app_module}")
print(f"  widget_name={app.widget_name}")

import importlib
ui_module = importlib.import_module(app.app_module + ".ui")
widget_class = getattr(ui_module, app.widget_name)
print(f"  resolved widget_class={widget_class.__name__}")

# Mock engine test
class MockEngine:
    def __getattr__(self, name): return None
widget_instance = widget_class(MockEngine(), MockEngine())
print(f"  instantiated={type(widget_instance).__name__}")
print(f"  has main_engine={hasattr(widget_instance, 'main_engine')}")

print()
print("=== ALL TESTS PASSED ===")