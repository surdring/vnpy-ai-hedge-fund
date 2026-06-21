"""AI signal real-time monitoring panel."""

from __future__ import annotations
from typing import Any
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QPushButton, QHBoxLayout, QLabel, QAbstractItemView,
)
from PySide6.QtCore import Qt, Signal


class SignalMonitor(QWidget):
    """Qt widget for displaying recent AI signals and decisions."""

    signal_received = Signal(dict)

    _COLUMNS = ["时间", "Ticker", "Agent", "信号", "置信度", "摘要"]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._signals: list[dict[str, Any]] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("AI 信号监控"))
        top_layout.addStretch()

        self.clear_btn = QPushButton("清空")
        self.clear_btn.clicked.connect(self._clear)
        top_layout.addWidget(self.clear_btn)

        layout.addLayout(top_layout)

        self.table = QTableWidget(0, len(self._COLUMNS))
        self.table.setHorizontalHeaderLabels(self._COLUMNS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table)

    def add_signal(self, signal_data: dict[str, Any]) -> None:
        """Add a new signal row to the table."""
        self._signals.append(signal_data)
        self.signal_received.emit(signal_data)

        row = self.table.rowCount()
        self.table.insertRow(row)

        timestamp = signal_data.get("timestamp", datetime.now().strftime("%H:%M:%S"))
        self.table.setItem(row, 0, self._make_item(str(timestamp)))

        ticker = signal_data.get("ticker", signal_data.get("symbol", "-"))
        self.table.setItem(row, 1, self._make_item(str(ticker)))

        agent = signal_data.get("agent", signal_data.get("agent_name", "-"))
        self.table.setItem(row, 2, self._make_item(str(agent)))

        signal_value = signal_data.get("signal", signal_data.get("action", "-"))
        self.table.setItem(row, 3, self._make_item(str(signal_value)))

        confidence = signal_data.get("confidence", signal_data.get("score", "-"))
        if isinstance(confidence, (int, float)):
            confidence = f"{confidence:.2f}"
        self.table.setItem(row, 4, self._make_item(str(confidence)))

        summary = signal_data.get("summary", signal_data.get("reason", "-"))
        self.table.setItem(row, 5, self._make_item(str(summary)))

        self.table.scrollToBottom()

    def _make_item(self, text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _clear(self) -> None:
        """Clear all signals from the table."""
        self._signals.clear()
        self.table.setRowCount(0)

    def get_recent(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the most recent n signals."""
        return self._signals[-n:]

    def clear(self) -> None:
        """Alias for _clear."""
        self._clear()