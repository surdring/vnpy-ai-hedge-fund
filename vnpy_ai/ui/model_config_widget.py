"""LLM model configuration panel."""

from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QLineEdit,
    QSlider, QLabel, QHBoxLayout, QGroupBox, QPushButton,
)
from PySide6.QtCore import Qt, Signal


class ModelConfigWidget(QWidget):
    """Qt widget for configuring LLM provider, model name, and temperature."""

    config_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._api_key_visible = False
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setSpacing(8)

        # Provider
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["OpenAI", "Ollama", "DeepSeek", "Anthropic", "Google", "llama.cpp"])
        self.provider_combo.setCurrentText("OpenAI")
        form_layout.addRow("Provider：", self.provider_combo)

        # Model name
        self.model_name_edit = QLineEdit()
        self.model_name_edit.setPlaceholderText("例如：gpt-4.1")
        self.model_name_edit.setText("gpt-4.1")
        form_layout.addRow("模型名称：", self.model_name_edit)

        # Temperature slider with range labels
        temp_container = QWidget()
        temp_layout = QVBoxLayout(temp_container)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        temp_layout.setSpacing(2)

        slider_row = QHBoxLayout()
        slider_row.setContentsMargins(0, 0, 0, 0)

        self.temp_slider = QSlider(Qt.Orientation.Horizontal)
        self.temp_slider.setRange(0, 200)
        self.temp_slider.setValue(70)
        self.temp_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temp_slider.setTickInterval(20)
        slider_row.addWidget(self.temp_slider)

        self.temp_label = QLabel("0.70")
        self.temp_label.setMinimumWidth(40)
        self.temp_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_row.addWidget(self.temp_label)

        temp_layout.addLayout(slider_row)

        range_row = QHBoxLayout()
        range_row.setContentsMargins(0, 0, 0, 0)
        range_min = QLabel("0.0")
        range_min.setStyleSheet("color: #6b7280; font-size: 11px;")
        range_max = QLabel("2.0")
        range_max.setAlignment(Qt.AlignmentFlag.AlignRight)
        range_max.setStyleSheet("color: #6b7280; font-size: 11px;")
        range_row.addWidget(range_min)
        range_row.addStretch()
        range_row.addWidget(range_max)
        temp_layout.addLayout(range_row)

        self.temp_slider.valueChanged.connect(self._on_temp_changed)
        form_layout.addRow("Temperature：", temp_container)

        # API Key with show/hide toggle
        api_key_row = QHBoxLayout()
        api_key_row.setContentsMargins(0, 0, 0, 0)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("输入 API Key")
        api_key_row.addWidget(self.api_key_edit)

        self.toggle_pwd_btn = QPushButton("\uE04F")  # eye-off icon placeholder
        self.toggle_pwd_btn.setFixedSize(28, 28)
        self.toggle_pwd_btn.setToolTip("显示 / 隐藏")
        self.toggle_pwd_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_pwd_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #6b7280;
                font-size: 14px;
                padding: 0;
            }
            QPushButton:hover { color: #9ca3af; }
        """)
        self.toggle_pwd_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_row.addWidget(self.toggle_pwd_btn)

        form_layout.addRow("API Key：", api_key_row)

        # Base URL
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("例如：http://localhost:8080/v1")
        form_layout.addRow("Base URL：", self.base_url_edit)

        layout.addLayout(form_layout)
        layout.addStretch()

    def _on_temp_changed(self, value: int) -> None:
        self.temp_label.setText(f"{value / 100:.2f}")
        self.config_changed.emit(self.get_config())

    def _toggle_api_key_visibility(self) -> None:
        """Toggle between password mask and plain text."""
        self._api_key_visible = not self._api_key_visible
        if self._api_key_visible:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_pwd_btn.setText("\uE063")  # eye icon
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_pwd_btn.setText("\uE04F")  # eye-off icon

    def get_config(self) -> dict[str, Any]:
        """Get current model configuration."""
        return {
            "provider": self.provider_combo.currentText(),
            "model_name": self.model_name_edit.text(),
            "temperature": self.temp_slider.value() / 100.0,
            "api_key": self.api_key_edit.text(),
            "base_url": self.base_url_edit.text(),
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
        if "base_url" in config:
            self.base_url_edit.setText(config["base_url"])
