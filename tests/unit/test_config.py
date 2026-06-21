from vnpy_ai.config import mask_api_keys


def test_mask_api_keys() -> None:
    assert mask_api_keys({"OPENAI_API_KEY": "sk-123456789"}) == {"OPENAI_API_KEY": "sk-****6789"}

