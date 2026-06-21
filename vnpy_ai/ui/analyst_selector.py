"""Analyst multi-select widget."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel,
)


def _load_analysts() -> list[tuple[str, str]]:
    """Load (display_name, key) pairs from catalog or runner.

    Falls back to an embedded list when vnpy_ai package is not importable
    to keep the widget usable in isolation.
    """

    try:
        from vnpy_ai.agents.catalog import ANALYST_ORDER
        return list(ANALYST_ORDER)
    except Exception:
        pass

    try:
        from vnpy_ai.workflow.runner import DEFAULT_ANALYSTS
        return [(key.replace("_", " ").title(), key) for key in DEFAULT_ANALYSTS]
    except Exception:
        pass

    # Embedded fallback so the widget still renders without the package
    return [
        ("Aswath Damodaran", "aswath_damodaran"),
        ("Ben Graham", "ben_graham"),
        ("Bill Ackman", "bill_ackman"),
        ("Cathie Wood", "cathie_wood"),
        ("Charlie Munger", "charlie_munger"),
        ("Michael Burry", "michael_burry"),
        ("Mohnish Pabrai", "mohnish_pabrai"),
        ("Nassim Taleb", "nassim_taleb"),
        ("Peter Lynch", "peter_lynch"),
        ("Phil Fisher", "phil_fisher"),
        ("Rakesh Jhunjhunwala", "rakesh_jhunjhunwala"),
        ("Stanley Druckenmiller", "stanley_druckenmiller"),
        ("Warren Buffett", "warren_buffett"),
        ("Technical Analyst", "technical_analyst"),
        ("Fundamentals Analyst", "fundamentals_analyst"),
        ("Growth Analyst", "growth_analyst"),
        ("News Sentiment Analyst", "news_sentiment_analyst"),
        ("Sentiment Analyst", "sentiment_analyst"),
        ("Valuation Analyst", "valuation_analyst"),
    ]


class AnalystSelector(QWidget):
    """Qt widget for multi-selecting analysts with checkboxes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._analysts: list[tuple[str, str]] = _load_analysts()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("分析师选择"))
        top_layout.addStretch()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self._select_all)
        top_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("全不选")
        self.select_none_btn.clicked.connect(self._select_none)
        top_layout.addWidget(self.select_none_btn)

        layout.addLayout(top_layout)

        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        for display_name, key in self._analysts:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, key)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        layout.addWidget(self.list_widget)

    def _select_all(self) -> None:
        """Check every analyst item."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Checked)

    def _select_none(self) -> None:
        """Uncheck every analyst item."""
        for i in range(self.list_widget.count()):
            self.list_widget.item(i).setCheckState(Qt.CheckState.Unchecked)

    def get_selected(self) -> list[str]:
        """Return the list of selected analyst keys."""
        selected: list[str] = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                key = item.data(Qt.ItemDataRole.UserRole)
                if isinstance(key, str):
                    selected.append(key)
        return selected

    def set_selected(self, analysts: list[str]) -> None:
        """Check items whose key appears in the given list."""
        wanted = set(analysts)
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            key = item.data(Qt.ItemDataRole.UserRole)
            state = Qt.CheckState.Checked if key in wanted else Qt.CheckState.Unchecked
            item.setCheckState(state)

    def get_config(self) -> dict[str, Any]:
        """Return selected analysts as a config dict."""
        return {"analysts": self.get_selected()}

    def set_config(self, config: dict[str, Any]) -> None:
        """Load selected analysts from a config dict."""
        analysts = config.get("analysts", [])
        if isinstance(analysts, list):
            self.set_selected([a for a in analysts if isinstance(a, str)])
