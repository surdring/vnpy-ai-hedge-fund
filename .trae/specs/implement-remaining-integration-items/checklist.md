# Checklist

## P0：核心决策链路打通
- [x] `vnpy_ai/tools/api.py` 存在并提供数据获取函数
- [x] `vnpy_ai/utils/` 目录包含 analysts.py、api_key.py、llm.py、display.py、progress.py、visualize.py
- [x] `vnpy_ai/llm/models.py` 支持 14 个 provider（Alibaba、Anthropic、DeepSeek、Google、Groq、Kimi、Meta、Mistral、OpenAI、Ollama、OpenRouter、GigaChat、Azure OpenAI、xAI）
- [x] `vnpy_ai/llm/api_models.json` 和 `ollama_models.json` 存在
- [x] 19 个分析师 Agent 的 `analyze()` 方法调用 LLM 返回 bullish/bearish/neutral 信号
- [x] `vnpy_ai/agents/risk_manager.py` 存在并提供 `RiskManagerAgent` 类
- [x] `vnpy_ai/agents/portfolio_manager.py` 存在并提供 `PortfolioManagerAgent` 类
- [x] `vnpy_ai/workflow/graph.py` 使用真实 RiskManagerAgent 和 PortfolioManagerAgent 替换内联占位符
- [x] 端到端决策链路测试通过：Agent 分析 → Risk 评估 → Portfolio 决策 → 订单派发

## P1：回测引擎与 GUI
- [x] `BacktestEngine.run()` 返回包含 status、metrics、trades 的完整结果（非固定空结果）
- [x] `VnpyAdapter.load_bars()` 通过 vnpy 数据库加载历史 BarData（非空列表）
- [x] `vnpy/trader/ui/mainwindow.py` 包含 "AI Agent" 菜单项

## P2：Web 后端与 UI 组件
- [x] `vnpy_ai_web/backend/services/graph.py` 调用 `vnpy_ai.workflow.graph.build_workflow_graph`
- [x] `vnpy_ai_web/backend/services/agent_service.py` 调用 `vnpy_ai.agents.catalog`
- [x] `vnpy_ai_web/backend/services/backtest_service.py` 调用 `vnpy_ai.backtesting.engine.BacktestEngine`
- [x] `vnpy_ai/ui/setting_widget.py` 提供真实 PySide6 配置面板
- [x] `vnpy_ai/ui/analyst_selector.py` 提供真实 PySide6 多选组件
- [x] `vnpy_ai/ui/model_config_widget.py` 提供真实 PySide6 模型配置面板
- [x] `vnpy_ai/ui/signal_monitor.py` 提供真实 PySide6 信号监控面板

## P3：非阻塞项
- [x] `vnpy/trader/engine.py` 的 `MainEngine` 包含 `add_ai_agent()` 方法
- [x] 测试环境目录 `C:\Users\DELL\.vntrader\log\` 自动创建，`pytest tests/ --collect-only` 无错误

## 验证命令
- [x] `pytest tests/ -v` 全部通过（29 passed in 1.86s）
- [x] `python -c "from vnpy_ai.agents.risk_manager import RiskManagerAgent"` 成功
- [x] `python -c "from vnpy_ai.agents.portfolio_manager import PortfolioManagerAgent"` 成功
- [x] `python -c "from vnpy_ai.llm.models import get_available_providers"` 返回列表
