"""
RPC bridge between the VeighNa process and the AI Agent process.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

try:
    from vnpy.rpc import RpcClient, RpcServer
except ModuleNotFoundError:
    RpcClient = None  # type: ignore[assignment]
    RpcServer = None  # type: ignore[assignment]

from .models import RpcMessage

logger = logging.getLogger(__name__)

REQUEST_MARKET_DATA = "REQUEST_MARKET_DATA"
RESPONSE_MARKET_DATA = "RESPONSE_MARKET_DATA"
REQUEST_PORTFOLIO = "REQUEST_PORTFOLIO"
RESPONSE_PORTFOLIO = "RESPONSE_PORTFOLIO"
SUBMIT_ORDER = "SUBMIT_ORDER"
ORDER_STATUS = "ORDER_STATUS"
AGENT_SIGNAL = "AGENT_SIGNAL"
HEARTBEAT = "HEARTBEAT"


def make_address(host: str, port: int) -> str:
    """Create a TCP ZMQ address."""

    return f"tcp://{host}:{port}"


@dataclass
class RpcAddresses:
    """RPC address pair."""

    rep: str
    pub: str


class AiRpcServer:
    """Small typed wrapper around vnpy.rpc.RpcServer."""

    def __init__(self) -> None:
        if RpcServer is None:
            raise RuntimeError("pyzmq is required for RPC bridge")
        self.server = RpcServer()

    def register(self, func: Callable[..., Any]) -> None:
        self.server.register(func)

    def start(self, rep_address: str, pub_address: str) -> None:
        self.server.start(rep_address, pub_address)

    def stop(self) -> None:
        self.server.stop()
        self.server.join()

    def publish(self, message_type: str, payload: dict[str, Any]) -> None:
        message = RpcMessage(type=message_type, payload=payload)
        self.server.publish(message_type, message.model_dump(mode="json"))


class AiRpcClient(RpcClient if RpcClient is not None else object):  # type: ignore[misc]
    """RPC client that stores pushed messages for consumers."""

    def __init__(self) -> None:
        if RpcClient is None:
            raise RuntimeError("pyzmq is required for RPC bridge")
        super().__init__()
        self.messages: list[RpcMessage] = []
        self.connected: bool = False

    def callback(self, topic: str, data: Any) -> None:
        if isinstance(data, dict) and "type" in data:
            self.messages.append(RpcMessage(**data))

    def on_disconnected(self) -> None:
        self.connected = False


def rpc_message(message_type: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a JSON-serializable RPC message."""

    return RpcMessage(type=message_type, payload=payload or {}).model_dump(mode="json")


class RpcBridge:
    """RPC bridge with reconnect, heartbeat, and offline message buffering."""

    def __init__(self) -> None:
        self._connected: bool = False
        self._message_buffer: collections.deque[dict[str, Any]] = collections.deque(maxlen=1000)
        self._heartbeat_timer: threading.Timer | None = None
        self._missed_heartbeats: int = 0

    # ── connection lifecycle ──────────────────────────────────────────

    def connect(self) -> None:
        """Mark as connected and start heartbeat."""
        self._connected = True
        self._start_heartbeat()

    def disconnect(self) -> None:
        """Mark as disconnected and stop heartbeat."""
        self._connected = False
        self._stop_heartbeat()

    # ── messaging ─────────────────────────────────────────────────────

    def send_message(self, message: dict[str, Any]) -> None:
        """Send a message, buffering offline messages for later replay."""
        if not self._connected:
            self._message_buffer.append(message)
            return
        try:
            self._do_send(message)
        except (OSError, ConnectionError):
            self._reconnect()
            try:
                self._do_send(message)
            except (OSError, ConnectionError):
                self._message_buffer.append(message)

    def send_status(self, status_msg: dict[str, Any]) -> None:
        """Convenience wrapper that sends a status-typed message."""
        self.send_message({"type": "status", "payload": status_msg})

    def send_with_retry(self, message: dict[str, Any], max_retries: int = 3) -> bool:
        """Send a message with retry logic.

        Tries to send the message. On failure, retries up to max_retries
        times with a 1s delay between retries. On final failure, logs the
        error and returns False. Returns True on success.

        Args:
            message: The message dict to send.
            max_retries: Maximum number of retry attempts (default 3).

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        last_error: Exception | None = None
        for attempt in range(max_retries + 1):
            try:
                self.send_message(message)
                return True
            except (OSError, ConnectionError, RuntimeError) as e:
                last_error = e
                if attempt < max_retries:
                    logger.warning(
                        "RPC send failed (attempt %d/%d), retrying in 1s: %s",
                        attempt + 1,
                        max_retries + 1,
                        e,
                    )
                    time.sleep(1)
        logger.error(
            "RPC send failed after %d attempts: %s",
            max_retries + 1,
            last_error,
        )
        return False

    def _do_send(self, message: dict[str, Any]) -> None:
        """Actual send implementation (placeholder for RPC client integration)."""
        # In production this delegates to the RPC client transport.
        pass

    # ── reconnect with exponential backoff (Task 4) ───────────────────

    def _reconnect(self, max_retries: int = 5) -> None:
        """Attempt reconnection with exponential backoff: 1s, 2s, 4s, 8s, 16s."""
        for i in range(max_retries):
            wait = 2 ** i
            logger.info("RPC reconnect attempt %d/%d, waiting %ds", i + 1, max_retries, wait)
            time.sleep(wait)
            try:
                self.connect()
                self._flush_buffer()
                return
            except (OSError, ConnectionError):
                continue
        self._notify_connection_lost()

    def _notify_connection_lost(self) -> None:
        """Log warning when connection is lost after all retries exhausted."""
        logger.warning("RPC connection lost after max retries")

    # ── heartbeat (Task 5) ────────────────────────────────────────────

    def _start_heartbeat(self, interval: int = 10) -> None:
        """Start a periodic heartbeat timer."""
        self._missed_heartbeats = 0
        self._heartbeat_timer = threading.Timer(interval, self._heartbeat_callback)
        self._heartbeat_timer.start()

    def _stop_heartbeat(self) -> None:
        """Cancel the heartbeat timer if active."""
        if self._heartbeat_timer is not None:
            self._heartbeat_timer.cancel()
            self._heartbeat_timer = None

    def _heartbeat_callback(self) -> None:
        """Send heartbeat; if 3+ consecutive heartbeats missed, trigger reconnect."""
        self.send_message({"type": "heartbeat"})
        self._missed_heartbeats += 1
        if self._missed_heartbeats >= 3:
            self._reconnect()
        else:
            self._start_heartbeat()

    # ── offline message buffer (Task 6) ───────────────────────────────

    def _flush_buffer(self) -> None:
        """Replay all buffered messages after reconnection."""
        while self._message_buffer:
            msg = self._message_buffer.popleft()
            try:
                self._do_send(msg)
            except (OSError, ConnectionError):
                self._message_buffer.appendleft(msg)
                break
