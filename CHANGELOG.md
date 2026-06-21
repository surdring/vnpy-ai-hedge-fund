# Changelog

## [Unreleased]
### Added
- Initial vnpy_ai integration package
- AiHedgeFundApp and AiHedgeFundEngine
- DataAdapter, OrderAdapter, EventAdapter, RpcBridge
- LangGraph workflow graph with 19 analyst agents
- LLM model factory with multi-provider support
- Backtesting engine with performance metrics
- Web backend with REST API
- Desktop GUI components (PySide6)
- Docker deployment support
- Comprehensive test suite (28 tests)

### Fixed
- send_decision() return value handling (P0)
- on_market_event() throttling and daily frequency support (P0)
- Event constants duplication (P1)
- Config path dependency on CWD (P1)
- Fallback decision confidence value (P1)