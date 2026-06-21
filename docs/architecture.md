# Architecture

`vnpy_ai` is a VeighNa plugin that keeps AI Agent execution isolated from the main trading process.

- VeighNa remains the source of truth for market data, orders, positions, accounts and events.
- `vnpy_ai` adapts VeighNa data into AI Hedge Fund compatible models.
- Optional LangChain/LangGraph dependencies belong to the isolated Agent process.
- Auto trading is disabled by default; decisions are emitted as events unless explicitly enabled.

