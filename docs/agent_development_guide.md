# Agent Development Guide

New agents must use `vnpy_ai.data_adapter` for data access and return structured decisions or analyst signals.

Do not read API keys directly in agents. Keys must come from runtime configuration and must be masked before any frontend response.

