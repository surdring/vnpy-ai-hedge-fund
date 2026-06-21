"""Agent parameter configuration panel."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QDoubleSpinBox,
    QSpinBox, QCheckBox, QGroupBox, QScrollArea,
)

from .analyst_selector import AnalystSelector
from .model_config_widget import ModelConfigWidget


class SettingWidget(QWidget):
    """Qt widget for configuring AI Agent workflow parameters."""

    TRIGGER_FREQUENCY = ["daily", "15min", "tick", "bar"]
    FALLBACK_STRATEGIES = ["hold", "sma_cross"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(4, 4, 4, 4)

        # Basic parameters group
        basic_group = QGroupBox("基础参数")
        form_layout = QFormLayout(basic_group)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(self.TRIGGER_FREQUENCY)
        self.trigger_combo.setCurrentText("daily")
        form_layout.addRow("触发频率:", self.trigger_combo)

        self.position_spin = QDoubleSpinBox()
        self.position_spin.setRange(0.0, 1.0)
        self.position_spin.setSingleStep(0.05)
        self.position_spin.setValue(0.2)
        self.position_spin.setDecimals(2)
        form_layout.addRow("仓位上限:", self.position_spin)

        self.auto_trade_check = QCheckBox("启用自动交易")
        form_layout.addRow("", self.auto_trade_check)

        self.cooldown_spin = QSpinBox()
        self.cooldown_spin.setRange(0, 86400)
        self.cooldown_spin.setSingleStep(10)
        self.cooldown_spin.setValue(60)
        self.cooldown_spin.setSuffix(" s")
        form_layout.addRow("信号冷却时间:", self.cooldown_spin)

        self.fallback_combo = QComboBox()
        self.fallback_combo.addItems(self.FALLBACK_STRATEGIES)
        self.fallback_combo.setCurrentText("hold")
        form_layout.addRow("降级策略:", self.fallback_combo)

        layout.addWidget(basic_group)

        # Analyst selector group
        analyst_group = QGroupBox("分析师选择")
        analyst_layout = QVBoxLayout(analyst_group)
        self.analyst_selector = AnalystSelector()
        analyst_layout.addWidget(self.analyst_selector)
        layout.addWidget(analyst_group)

        # LLM model config group
        model_group = QGroupBox("LLM 模型配置")
        model_layout = QVBoxLayout(model_group)
        self.model_config = ModelConfigWidget()
        model_layout.addWidget(self.model_config)
        layout.addWidget(model_group)

        layout.addStretch()

        scroll.setWidget(inner)
        outer_layout.addWidget(scroll)

    def get_config(self) -> dict[str, Any]:
        """Get current agent configuration."""
        return {
            "trigger_frequency": self.trigger_combo.currentText(),
            "position_limit": self.position_spin.value(),
            "auto_trade": self.auto_trade_check.isChecked(),
            "cooldown_seconds": self.cooldown_spin.value(),
            "fallback_strategy": self.fallback_combo.currentText(),
            "analysts": self.analyst_selector.get_selected(),
            "model": self.model_config.get_config(),
        }

    def set_config(self, config: dict[str, Any]) -> None:
        """Load agent configuration from dict."""
        if "trigger_frequency" in config:
            idx = self.trigger_combo.findText(config["trigger_frequency"])
            if idx >= 0:
                self.trigger_combo.setCurrentIndex(idx)
        if "position_limit" in config:
            self.position_spin.setValue(float(config["position_limit"]))
        if "auto_trade" in config:
            self.auto_trade_check.setChecked(bool(config["auto_trade"]))
        if "cooldown_seconds" in config:
            self.cooldown_spin.setValue(int(config["cooldown_seconds"]))
        if "fallback_strategy" in config:
            idx = self.fallback_combo.findText(config["fallback_strategy"])
            if idx >= 0:
                self.fallback_combo.setCurrentIndex(idx)
        if "analysts" in config and isinstance(config["analysts"], list):
            self.analyst_selector.set_selected(
                [a for a in config["analysts"] if isinstance(a, str)]
            )
        if "model" in config and isinstance(config["model"], dict):
            self.model_config.set_config(config["model"])
