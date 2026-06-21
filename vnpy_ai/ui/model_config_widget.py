"""LLM model configuration panel."""

from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QSlider, QLabel, QHBoxLayout, QGroupBox,
)
from PySide6.QtCore import Qt, Signal


class ModelConfigWidget(QWidget):
    """Qt widget for configuring LLM provider, model name, and temperature."""

    config_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        group = QGroupBox("LLM 模型配置")
        form_layout = QFormLayout(group)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "Ollama", "DeepSeek", "Anthropic", "Google"])
        self.provider_combo.setCurrentText("OpenAI")
        form_layout.addRow("Provider:", self.provider_combo)

        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("例如: gpt-4.1")
        self.model_name_edit.setText("gpt-4.1")
        form_layout.addRow("模型名称:", self.model_name_edit)

        temp_layout = QHBoxLayout()
        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(70)
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(20)
        temp_layout.addWidget(self.temp_slider)

        self.temp_label = QLabel("0.70")
        self.temp_label.setMinimumWidth(40)
        temp_layout.addWidget(self.temp_label)

        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        form_layout.addRow("Temperature:", temp_layout)

        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入 API Key")
        form_layout.addRow("API Key:", self.api_key_edit)

        layout.addWidget(group)
        layout.addStretch()

    def _on_temp_changed(self, value: int) -> None:
        self.temp_label.setText(f"{value / 100:.2f}")

    def get_config(self) -> dict[str, Any]:
        """Get current model configuration."""
        return {
            "provider": self.provider_combo.currentText(),
            "model_name": self.model_name_edit.text(),
            "temperature": self.temp_slider.value() / 100.0,
            "api_key": self.api_key_edit.text(),
        }

    def set_config(self, config: dict[str, Any]) -> None:
        """Load model configuration from dict."""
        if "provider" in config:
            idx = self.provider_combo.findText(config["provider"])
            if idx >= 0:
                self.provider_combo.setCurrentIndex(idx)
        if "model_name" in config:
            self.model_name_edit.setText(config["model_name"])
        if "temperature" in config:
            self.temp_slider.setValue(int(config["temperature"] * 100))
        if "api_key" in config:
            self.api_key_edit.setText(config["api_key"])