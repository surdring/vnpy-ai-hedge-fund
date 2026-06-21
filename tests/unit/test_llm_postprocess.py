from vnpy_ai.llm.postprocess import clean_reasoning_text, extract_json_from_response


def test_clean_reasoning_text_removes_think_block() -> None:
    assert clean_reasoning_text("<think>hidden</think>{\"ok\": true}") == '{"ok": true}'


def test_extract_json_from_markdown() -> None:
    assert extract_json_from_response("```json\n{\"ok\": true}\n```") == {"ok": True}

