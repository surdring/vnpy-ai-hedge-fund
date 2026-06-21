"""LLM model factory with lazy loading."""

from __future__ import annotations

from typing import Any
import logging

logger = logging.getLogger(__name__)


def create_model(
    provider: str = "OpenAI",
    model_name: str = "gpt-4.1",
    **kwargs: Any,
) -> Any:
    """Create a LangChain chat model instance.

    Args:
        provider: LLM provider name (OpenAI, Anthropic, Ollama, Google, DeepSeek,
            Groq, Alibaba, Kimi, Meta, Mistral, OpenRouter, GigaChat, Azure OpenAI,
            xAI). Case-insensitive.
        model_name: Model identifier string.
        **kwargs: Additional provider-specific parameters (api_key, base_url, etc.).

    Returns:
        LangChain chat model instance, or None if the required package is
        unavailable or the provider is unknown.
    """
    try:
        from langchain_core.language_models.chat_models import BaseChatModel  # noqa: F401
    except ImportError:
        logger.warning(
            "langchain_core not installed; LLM model creation disabled. "
            "Install with: pip install langchain-core langchain-openai"
        )
        return None

    provider = provider.lower()

    try:
        if provider == "openai":
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                logger.warning("langchain_openai not installed")
                return None
            return ChatOpenAI(model=model_name, **kwargs)

        elif provider in ("azure", "azure openai"):
            try:
                from langchain_openai import AzureChatOpenAI
            except ImportError:
                logger.warning(
                    "langchain_openai not installed; AzureChatOpenAI unavailable"
                )
                return None
            return AzureChatOpenAI(model=model_name, **kwargs)

        elif provider == "anthropic":
            try:
                from langchain_anthropic import ChatAnthropic
            except ImportError:
                logger.warning("langchain_anthropic not installed")
                return None
            return ChatAnthropic(model=model_name, **kwargs)  # type: ignore[call-arg]

        elif provider == "ollama":
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                logger.warning("langchain_ollama not installed")
                return None
            return ChatOllama(model=model_name, **kwargs)

        elif provider == "google":
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
            except ImportError:
                logger.warning("langchain_google_genai not installed")
                return None
            return ChatGoogleGenerativeAI(model=model_name, **kwargs)

        elif provider == "deepseek":
            try:
                from langchain_deepseek import ChatDeepSeek
            except ImportError:
                logger.warning("langchain_deepseek not installed")
                return None
            return ChatDeepSeek(model=model_name, **kwargs)

        elif provider == "groq":
            try:
                from langchain_groq import ChatGroq
            except ImportError:
                logger.warning("langchain_groq not installed")
                return None
            return ChatGroq(model=model_name, **kwargs)

        elif provider == "alibaba":
            try:
                from langchain_community.chat_models.tongyi import ChatTongyi
            except ImportError:
                logger.warning(
                    "langchain_community (ChatTongyi) not installed; "
                    "Alibaba provider unavailable"
                )
                return None
            return ChatTongyi(model=model_name, **kwargs)

        elif provider in ("kimi", "moonshot"):
            # Kimi (Moonshot) exposes an OpenAI-compatible endpoint.
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                logger.warning(
                    "langchain_openai not installed; Kimi/Moonshot unavailable"
                )
                return None
            kwargs.setdefault("base_url", "https://api.moonshot.ai/v1")
            return ChatOpenAI(model=model_name, **kwargs)

        elif provider == "meta":
            # Meta Llama models are typically served via Ollama (or Together AI).
            # Reuse ChatOllama by default; callers may override base_url via kwargs.
            try:
                from langchain_ollama import ChatOllama
            except ImportError:
                logger.warning(
                    "langchain_ollama not installed; Meta provider unavailable"
                )
                return None
            return ChatOllama(model=model_name, **kwargs)

        elif provider == "mistral":
            try:
                from langchain_mistralai import ChatMistralAI
            except ImportError:
                logger.warning("langchain_mistralai not installed")
                return None
            return ChatMistralAI(model=model_name, **kwargs)

        elif provider == "openrouter":
            # OpenRouter exposes an OpenAI-compatible endpoint.
            try:
                from langchain_openai import ChatOpenAI
            except ImportError:
                logger.warning(
                    "langchain_openai not installed; OpenRouter unavailable"
                )
                return None
            kwargs.setdefault("base_url", "https://openrouter.ai/api/v1")
            return ChatOpenAI(model=model_name, **kwargs)

        elif provider == "gigachat":
            try:
                from langchain_gigachat import GigaChat
            except ImportError:
                logger.warning("langchain_gigachat not installed")
                return None
            return GigaChat(model=model_name, **kwargs)

        elif provider == "xai":
            try:
                from langchain_xai import ChatXAI
            except ImportError:
                logger.warning("langchain_xai not installed")
                return None
            return ChatXAI(model=model_name, **kwargs)

        else:
            logger.warning(f"Unknown LLM provider: {provider}")
            return None

    except Exception as e:
        logger.error(f"Failed to create LLM model: {e}")
        return None


def get_available_providers() -> list[str]:
    """Return list of available LLM providers based on installed packages.

    A provider is considered available when its required LangChain integration
    package can be imported. Providers that share a dependency (e.g. OpenAI,
    Azure OpenAI, OpenRouter and Kimi all rely on ``langchain_openai``) are
    reported together when that dependency is present.
    """
    available: list[str] = []
    # OpenAI, Azure OpenAI, OpenRouter and Kimi all rely on langchain_openai
    # (Kimi/OpenRouter use ChatOpenAI with a custom base_url).
    try:
        import langchain_openai  # noqa: F401
        available.extend(["openai", "azure", "openrouter", "kimi"])
    except ImportError:
        pass
    try:
        import langchain_anthropic  # noqa: F401
        available.append("anthropic")
    except ImportError:
        pass
    # Ollama and Meta both rely on langchain_ollama (Meta reuses ChatOllama).
    try:
        import langchain_ollama  # noqa: F401
        available.extend(["ollama", "meta"])
    except ImportError:
        pass
    try:
        import langchain_google_genai  # noqa: F401
        available.append("google")
    except ImportError:
        pass
    try:
        import langchain_deepseek  # noqa: F401
        available.append("deepseek")
    except ImportError:
        pass
    try:
        import langchain_groq  # noqa: F401
        available.append("groq")
    except ImportError:
        pass
    try:
        import langchain_mistralai  # noqa: F401
        available.append("mistral")
    except ImportError:
        pass
    try:
        import langchain_xai  # noqa: F401
        available.append("xai")
    except ImportError:
        pass
    try:
        import langchain_gigachat  # noqa: F401
        available.append("gigachat")
    except ImportError:
        pass
    try:
        from langchain_community.chat_models.tongyi import ChatTongyi  # noqa: F401
        available.append("alibaba")
    except ImportError:
        pass
    return available
