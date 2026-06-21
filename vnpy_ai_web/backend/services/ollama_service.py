"""Ollama service for managing local LLM models."""

from __future__ import annotations


class OllamaService:
    """Service for interacting with Ollama LLM server."""

    def list_models(self) -> list[dict]:
        """List available Ollama models (stub)."""
        return [
            {"name": "llama3", "size": "4.7GB", "modified": "2024-01-01"},
            {"name": "mistral", "size": "4.1GB", "modified": "2024-01-01"},
            {"name": "codellama", "size": "3.8GB", "modified": "2024-01-01"},
        ]

    def check_health(self) -> dict:
        """Check Ollama server health (stub)."""
        return {"status": "ok", "endpoint": "http://localhost:11434"}
