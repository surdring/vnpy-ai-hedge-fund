"""
VeighNa AI Hedge Fund integration package.
"""

from pathlib import Path
import sys


_REPO_VNPY_PATH = Path(__file__).resolve().parent.parent / "vnpy"
if (_REPO_VNPY_PATH / "vnpy").exists():
    path_text = str(_REPO_VNPY_PATH)
    if path_text not in sys.path:
        sys.path.insert(0, path_text)

__version__ = "0.1.0"
