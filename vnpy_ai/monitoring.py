"""
Runtime monitoring helpers.
"""

from __future__ import annotations

import json
import logging
import socket
import sys
from datetime import datetime
from pathlib import Path


def is_port_open(host: str, port: int, timeout: float = 0.2) -> bool:
    """Check whether a local TCP port is reachable."""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def read_pid_file(path: str | Path) -> int | None:
    """Read a PID file if present."""

    pid_path = Path(path)
    if not pid_path.exists():
        return None
    try:
        return int(pid_path.read_text(encoding="utf-8").strip())
    except ValueError:
        return None


def setup_structured_logging(level: int = logging.INFO) -> None:
    """Configure stdout JSON structured logging."""

    class JsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_entry: dict[str, str] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if record.exc_info and record.exc_info[1]:
                log_entry["exception"] = str(record.exc_info[1])
            return json.dumps(log_entry, default=str)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [handler]

