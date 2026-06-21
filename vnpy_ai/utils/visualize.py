"""
Visualization helpers for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/visualize.py (MIT License, Virat Singh).
Uses `pathlib.Path` for cross-platform path handling and degrades gracefully
when `langgraph`/`langchain_core` are not installed.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_graph_as_png(app: Any, output_file_path: str | Path = "") -> bool:
    """Render a LangGraph workflow graph to a PNG file.

    Args:
        app: Compiled LangGraph instance.
        output_file_path: Target file path; defaults to `graph.png` in cwd.

    Returns:
        True if the file was written, False if dependencies are missing or
        rendering failed.
    """
    try:
        from langchain_core.runnables.graph import MermaidDrawMethod  # noqa: F401
    except ImportError:
        logger.warning(
            "langchain_core not installed; cannot render graph PNG. "
            "Install with: pip install langchain-core langgraph"
        )
        return False

    try:
        png_image = app.get_graph().draw_mermaid_png(draw_method=MermaidDrawMethod.API)
    except Exception:
        logger.warning("Failed to render graph PNG", exc_info=True)
        return False

    file_path = Path(output_file_path) if output_file_path else Path("graph.png")
    try:
        file_path.write_bytes(png_image)
        return True
    except Exception:
        logger.warning("Failed to write graph PNG to %s", file_path, exc_info=True)
        return False
