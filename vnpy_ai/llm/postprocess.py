"""
LLM output post-processing.
"""

from __future__ import annotations

import json
import re
from typing import Any


THINKING_PATTERNS = [
    re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE),
    re.compile(r"<reasoning>.*?</reasoning>", re.DOTALL | re.IGNORECASE),
]


def clean_reasoning_text(text: str, max_chars: int = 4000) -> str:
    """Remove common reasoning blocks and trim duplicated whitespace."""

    cleaned = text
    for pattern in THINKING_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned[:max_chars]


def extract_json_from_response(content: Any) -> dict[str, Any] | None:
    """Extract the first JSON object from common LLM response shapes."""

    if isinstance(content, dict):
        return content
    if isinstance(content, list):
        text_parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                text_parts.append(block)
            elif isinstance(block, dict):
                text_parts.append(str(block.get("text") or block.get("content") or ""))
        content = "\n".join(text_parts)
    if not isinstance(content, str):
        return None

    text = clean_reasoning_text(content)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidates = [fenced.group(1)] if fenced else []
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, char in enumerate(text[start:], start):
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start:i + 1])
                    break

    for candidate in candidates + [text]:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None

