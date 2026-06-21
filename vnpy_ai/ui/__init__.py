"""UI components for AI Hedge Fund."""
from typing import Any

from PySide6.QtCore import QSize, QEvent
from PySide6.QtWidgets import QWidget

from .setting_widget import SettingWidget
from .analyst_selector import AnalystSelector
from .model_config_widget import ModelConfigWidget
from .signal_monitor import SignalMonitor


class AiHedgeFundWidget(SettingWidget):
    """Main widget registered as the VeighNa app UI."""

    def __init__(self, main_engine: Any, event_engine: Any) -> None:
        """VeighNa passes (main_engine, event_engine) to dock widgets."""
        super().__init__()
        self.main_engine = main_engine
        self.event_engine = event_engine
        self._first_show = True

    def showEvent(self, event) -> None:
        """Force initial window size on first show (overrides cached layout)."""
        super().showEvent(event)
        if self._first_show:
            self._first_show = False
            self.resize(620, 780)


__all__ = ["SettingWidget", "AnalystSelector", "ModelConfigWidget", "SignalMonitor", "AiHedgeFundWidget"]
