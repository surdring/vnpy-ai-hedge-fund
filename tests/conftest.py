"""Pytest configuration and fixtures for vnpy-ai-hedge-fund tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Module-level setup: executed immediately when conftest.py is imported,
# BEFORE any test module imports (including vnpy.trader.engine which
# triggers logger.py to open log files).
_log_dir = Path(os.environ.get("VNPY_LOG_DIR", Path.home() / ".vntrader" / "log"))
_log_dir.mkdir(parents=True, exist_ok=True)

_data_dir = Path.home() / ".vntrader"
_data_dir.mkdir(parents=True, exist_ok=True)

# Mock talib module if not installed (vnpy.trader.utility imports it)
if "talib" not in sys.modules:
    try:
        import talib  # noqa: F401
    except ImportError:
        talib_mock = MagicMock()
        sys.modules["talib"] = talib_mock

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Ensure required directories exist before test collection."""
    # Re-ensure (idempotent) in case home dir was cleaned between runs
    _log_dir.mkdir(parents=True, exist_ok=True)
    _data_dir.mkdir(parents=True, exist_ok=True)
