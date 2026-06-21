"""
VeighNa AI Desktop UI Launcher
Patches pathlib to work around Trae sandbox signature_bootstrap issue.
"""
import os
import sys
import pathlib

# ── Patch pathlib.Path to work around signature_bootstrap ──────────────
# The sandbox intercepts Path.__new__ and can pass None arguments when
# PySide6's _setupQtDirectories() resolves Qt DLL paths.
# ────────────────────────────────────────────────────────────────────────
_original_path_new = pathlib.Path.__new__


def _patched_path_new(cls, *args, **kwargs):
    """Wrap Path.__new__ to convert None positional args to empty string."""
    cleaned = tuple("" if a is None else a for a in args)
    return _original_path_new(cls, *cleaned, **kwargs)


pathlib.Path.__new__ = _patched_path_new

# Patch PurePath derivatives too
for cls_name in ("PureWindowsPath", "PurePosixPath", "PurePath"):
    cls = getattr(pathlib, cls_name, None)
    if cls and cls is not pathlib.Path and cls.__new__ is not object.__new__:
        try:
            orig = cls.__new__

            def _make_wrapper(original):
                def _wrapped(cls2, *args, **kwargs):
                    cleaned = tuple("" if a is None else a for a in args)
                    return original(cls2, *cleaned, **kwargs)
                return _wrapped
            cls.__new__ = _make_wrapper(orig)
        except (AttributeError, TypeError):
            pass

# ── Run original entry point ───────────────────────────────────────────
# vnpy.examples is NOT a package (no __init__.py), so add its directory
# to sys.path and import run.py directly.
_RUN_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vnpy", "examples", "veighna_trader")
sys.path.insert(0, _RUN_DIR)


def main():
    import run
    run.main()


if __name__ == "__main__":
    main()