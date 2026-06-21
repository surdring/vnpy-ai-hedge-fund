from vnpy_ai.rpc_bridge import HEARTBEAT, rpc_message


def test_rpc_message_shape() -> None:
    message = rpc_message(HEARTBEAT, {"ok": True})
    assert message["type"] == HEARTBEAT
    assert message["payload"] == {"ok": True}
    assert "request_id" in message
    assert "timestamp" in message

