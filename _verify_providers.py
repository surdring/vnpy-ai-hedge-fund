"""Temporary verification script for LLM providers."""
import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")

# Check installed langchain packages
langchain_pkgs = []
for pkg_name in [
    "langchain", "langchain_core", "langchain_openai", "langchain_anthropic",
    "langchain_ollama", "langchain_google_genai", "langchain_deepseek",
    "langchain_groq", "langchain_mistralai", "langchain_xai",
    "langchain_gigachat", "langchain_community",
]:
    try:
        __import__(pkg_name)
        langchain_pkgs.append(pkg_name)
    except ImportError:
        pass
print(f"Installed langchain packages: {langchain_pkgs}")

from vnpy_ai.llm.models import get_available_providers
providers = get_available_providers()
print(f"Available providers: {providers}")
print(f"Count: {len(providers)}")
assert len(providers) >= 4, "At least 4 providers should be available"
print("VERIFICATION PASSED")
