"""
LLM helper functions for the VeighNa AI Hedge Fund integration.

Adapted from ai-hedge-fund/src/utils/llm.py (MIT License, Virat Singh).
Uses `vnpy_ai.llm.models.create_model()` instead of the upstream
`get_model()`/`get_model_info()` pair, and reuses the shared
`extract_json_from_response()` post-processor.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from vnpy_ai.llm.models import create_model
from vnpy_ai.llm.postprocess import extract_json_from_response

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Default model used when state does not carry agent-specific configuration.
DEFAULT_MODEL_NAME = "gpt-4.1"
DEFAULT_MODEL_PROVIDER = "openai"


def call_llm(
    prompt: Any,
    pydantic_model: type[T],
    agent_name: str | None = None,
    state: dict[str, Any] | None = None,
    max_retries: int = 3,
    default_factory: Callable[[], T] | None = None,
) -> T:
    """Call an LLM with retry logic and structured output.

    Args:
        prompt: The prompt to send to the LLM (str or ChatPromptValue).
        pydantic_model: The Pydantic model class to structure the output.
        agent_name: Optional agent name for progress updates.
        state: Optional workflow state dict for model config and API keys.
        max_retries: Maximum number of retries (default 3).
        default_factory: Optional factory returning a fallback response.

    Returns:
        An instance of `pydantic_model`. On persistent failure, returns
        either `default_factory()` or a `create_default_response()` value.
    """
    from vnpy_ai.utils.progress import progress

    model_name, model_provider = get_agent_model_config(state, agent_name)
    api_keys = _extract_api_keys(state)
    base_url = _extract_base_url(state)

    llm = create_model(
        provider=model_provider,
        model_name=model_name,
        **(api_keys or {}),
        **({"base_url": base_url} if base_url else {}),
    )

    if llm is None:
        logger.warning(
            "LLM unavailable for agent=%s; returning default response",
            agent_name,
        )
        if default_factory is not None:
            return default_factory()
        return create_default_response(pydantic_model)

    # Try structured output first; fall back to manual JSON parsing.
    structured_llm = None
    try:
        structured_llm = llm.with_structured_output(pydantic_model)
    except Exception:
        logger.debug(
            "with_structured_output unavailable for agent=%s; using raw invoke",
            agent_name,
            exc_info=True,
        )
        structured_llm = None

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            if structured_llm is not None:
                result = structured_llm.invoke(prompt)
                if isinstance(result, BaseModel):
                    return cast(T, result)
                if isinstance(result, dict):
                    return pydantic_model(**result)

            # Fallback: raw invoke + manual JSON extraction.
            raw = llm.invoke(prompt)
            content = getattr(raw, "content", raw)
            parsed = extract_json_from_response(content)
            if parsed is not None:
                return pydantic_model(**parsed)

            raise ValueError("Failed to parse structured output from LLM response")

        except Exception as exc:
            last_error = exc
            if agent_name:
                progress.update_status(
                    agent_name, None, f"Error - retry {attempt + 1}/{max_retries}"
                )
            logger.warning(
                "LLM call failed for agent=%s attempt=%d/%d: %s",
                agent_name,
                attempt + 1,
                max_retries,
                exc,
            )

    logger.error(
        "LLM call failed after %d attempts for agent=%s: %s",
        max_retries,
        agent_name,
        last_error,
    )
    if default_factory is not None:
        return default_factory()
    return create_default_response(pydantic_model)


def create_default_response(model_class: type[T]) -> T:
    """Create a safe default response based on the model's field types."""
    default_values: dict[str, Any] = {}
    for field_name, field in model_class.model_fields.items():
        annotation = field.annotation
        if annotation is str:
            default_values[field_name] = "Error in analysis, using default"
        elif annotation is float:
            default_values[field_name] = 0.0
        elif annotation is int:
            default_values[field_name] = 0
        elif annotation is bool:
            default_values[field_name] = False
        elif annotation is not None and hasattr(annotation, "__origin__") and annotation.__origin__ is dict:
            default_values[field_name] = {}
        elif annotation is not None and hasattr(annotation, "__origin__") and annotation.__origin__ is list:
            default_values[field_name] = []
        elif annotation is not None and hasattr(annotation, "__args__"):
            default_values[field_name] = annotation.__args__[0]
        else:
            default_values[field_name] = None
    return model_class(**default_values)


def get_agent_model_config(
    state: dict[str, Any] | None,
    agent_name: str | None,
) -> tuple[str, str]:
    """Resolve (model_name, model_provider) for an agent from state.

    Falls back to global config in `state.metadata`, then to module defaults.
    """
    if not state:
        return DEFAULT_MODEL_NAME, DEFAULT_MODEL_PROVIDER

    request = state.get("metadata", {}).get("request")
    if request is not None and hasattr(request, "get_agent_model_config"):
        try:
            model_name, model_provider = request.get_agent_model_config(agent_name)
            if model_name and model_provider:
                provider_str = (
                    model_provider.value
                    if hasattr(model_provider, "value")
                    else str(model_provider)
                )
                return model_name, provider_str
        except Exception:
            logger.debug("get_agent_model_config failed", exc_info=True)

    metadata = state.get("metadata", {})
    model_name = metadata.get("model_name") or DEFAULT_MODEL_NAME
    model_provider = metadata.get("model_provider") or DEFAULT_MODEL_PROVIDER
    if hasattr(model_provider, "value"):
        model_provider = model_provider.value
    return model_name, str(model_provider)


def _extract_api_keys(state: dict[str, Any] | None) -> dict[str, str]:
    """Extract API keys from state and return them as kwargs for create_model."""
    if not state:
        return {}
    request = state.get("metadata", {}).get("request")
    if request is None:
        return {}
    api_keys = getattr(request, "api_keys", None)
    if not api_keys:
        return {}
    # Map common key names to LangChain provider kwargs. create_model forwards
    # **kwargs to the underlying Chat* constructor, which accepts api_key.
    result: dict[str, str] = {}
    for key_name, value in api_keys.items():
        if not value:
            continue
        lower = key_name.lower()
        if "openai" in lower or "azure" in lower:
            result["api_key"] = value
        elif "anthropic" in lower:
            result["api_key"] = value
        elif "google" in lower or "gemini" in lower:
            result["google_api_key"] = value
        elif "ollama" in lower:
            # Ollama typically does not require a key; skip.
            continue
        else:
            result.setdefault("api_key", value)
    return result


def _extract_base_url(state: dict[str, Any] | None) -> str:
    """Extract base_url from state metadata."""
    if not state:
        return ""
    metadata = state.get("metadata", {})
    base_url = metadata.get("llm_base_url") or metadata.get("base_url") or ""
    return str(base_url).strip()


# Re-export for backwards compatibility with upstream imports.
__all__ = [
    "call_llm",
    "create_default_response",
    "get_agent_model_config",
    "extract_json_from_response",
    "json",
]
