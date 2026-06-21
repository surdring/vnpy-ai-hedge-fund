# Deployment Guide

1. Install core dependencies for VeighNa and `vnpy_ai`.
2. Keep `AI_AGENT_ENABLED=false` until data, LLM and risk controls are verified.
3. Use Ollama for local-first inference or provide cloud API keys through environment variables.
4. Start the VeighNa process and the Agent process on localhost ports `9001` and `9002`.
5. Run the 7-day production soak test before marking production acceptance complete.

