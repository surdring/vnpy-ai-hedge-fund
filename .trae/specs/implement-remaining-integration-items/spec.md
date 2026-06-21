# Implement Remaining Integration Items Spec

## Why
实现审查报告（`zheng-docs/实现审查报告.md`）识别出 13 项未实现的整合方案项，分布在 P0（核心决策链路断裂）、P1（回测/GUI）、P2（工具/LLM/Web/UI）、P3（非阻塞）四个优先级。当前架构骨架 ~85% 完成，但功能深度仅 ~60%：19 个 Agent 的 `analyze()` 返回固定 "neutral" 信号不调用 LLM，Risk/Portfolio Manager 为内联占位符，回测引擎为 stub，端到端决策链路完全断裂。本 spec 覆盖全部 13 项，按 P0→P1→P2→P3 顺序实现，目标是打通"框架可用"到"功能可用"的关键链路。

## What Changes
- **P0 核心决策链路**（3 项）：
  - 19 个分析师 Agent 的 `analyze()` 方法移植上游真实 LLM 调用逻辑（替换 stub）
  - 创建顶层 `vnpy_ai/agents/risk_manager.py` 和 `portfolio_manager.py`（替换 graph.py 内联占位符）
  - 打通端到端决策链路：数据获取 → Agent LLM 分析 → Risk 评估 → Portfolio 决策 → 订单派发
- **P1 回测与 GUI**（3 项）：
  - `BacktestEngine.run()` 实现真实回测逻辑（替换返回固定空结果）
  - `VnpyAdapter.load_bars()` 实现从 vnpy 数据库加载历史数据（替换返回空列表）
  - vnpy GUI `mainwindow.py` 新增 AI Agent 菜单入口
- **P2 工具与扩展**（5 项）：
  - 创建 `vnpy_ai/tools/` 目录（含 `api.py`）
  - 创建 `vnpy_ai/utils/` 目录（含 `analysts.py`、`api_key.py`、`llm.py`、`display.py`、`progress.py`、`visualize.py`）
  - LLM provider 从 4 个扩展到 14 个（Alibaba、Anthropic、DeepSeek、Google、Groq、Kimi、Meta、Mistral、OpenAI、Ollama、OpenRouter、GigaChat、Azure OpenAI、xAI）
  - 移植 `api_models.json` 和 `ollama_models.json` 到 `vnpy_ai/llm/`
  - Web 后端 services（`graph.py`、`agent_service.py`、`backtest_service.py`）替换 stub 为真实实现
  - UI 组件（`setting_widget.py`、`analyst_selector.py`、`model_config_widget.py`、`signal_monitor.py`）替换 stub 为真实 PySide6 界面
- **P3 非阻塞**（2 项）：
  - `vnpy/trader/engine.py` 新增 `add_ai_agent()` 方法
  - 修复测试环境目录缺失问题（`C:\Users\DELL\.vntrader\log\`）

## Impact
- Affected specs: 无（新 spec，与已存在的 `complete-all-remaining-items` 互补但更精准对齐审查报告）
- Affected code:
  - `vnpy_ai/agents/*.py`（19 个分析师，重写 analyze 方法）
  - `vnpy_ai/agents/risk_manager.py`、`portfolio_manager.py`（新建）
  - `vnpy_ai/workflow/graph.py`（替换内联占位符为真实节点）
  - `vnpy_ai/backtesting/engine.py`、`vnpy_adapter.py`（实现真实逻辑）
  - `vnpy_ai/llm/models.py`（扩展到 14 providers）
  - `vnpy_ai/llm/api_models.json`、`ollama_models.json`（新建）
  - `vnpy_ai/tools/`、`vnpy_ai/utils/`（新建目录）
  - `vnpy_ai/ui/*.py`（4 个组件实现真实界面）
  - `vnpy_ai_web/backend/services/*.py`（替换 stub）
  - `vnpy/trader/engine.py`（新增 add_ai_agent 方法）
  - `vnpy/trader/ui/mainwindow.py`（新增菜单项）
  - `tests/`（新增测试用例）

---

## ADDED Requirements

### P0：核心决策链路打通

#### Requirement: 19 个分析师 Agent 真实 LLM 调用
每个分析师 Agent 的 `analyze()` 方法 SHALL 通过 LLM 对获取的数据进行分析，返回具体的 bullish/bearish/neutral 信号、0-100 置信度和推理文本。实现方式为从 `ai-hedge-fund/src/agents/` 移植真实分析逻辑，适配为继承 `AgentBase` 的类方法，通过 `vnpy_ai/llm/models.py` 创建 LLM 实例，使用 `with_structured_output` 强制结构化输出。

#### Requirement: 顶层 Risk Manager 实现
`vnpy_ai/agents/risk_manager.py` SHALL 提供 `RiskManagerAgent` 类，继承 `AgentBase`，实现波动率计算、相关性分析、VaR 计算、仓位限制。从 `ai-hedge-fund/src/agents/risk_manager.py` 移植 `calculate_volatility_metrics`、`calculate_var`、`calculate_correlation_analysis` 等核心函数。

#### Requirement: 顶层 Portfolio Manager 实现
`vnpy_ai/agents/portfolio_manager.py` SHALL 提供 `PortfolioManagerAgent` 类，继承 `AgentBase`，实现信号综合评分、操作约束计算、最终决策生成。从 `ai-hedge-fund/src/agents/portfolio_manager.py` 移植 `PortfolioManagerOutput` 模型和决策逻辑。

#### Requirement: 工作流图替换占位符
`vnpy_ai/workflow/graph.py` SHALL 用真实的 `RiskManagerAgent` 和 `PortfolioManagerAgent` 实例替换 `_make_risk_manager_node()` 和 `_make_portfolio_manager_node()` 内联占位符。

#### Scenario: 端到端决策链路
- **WHEN** 工作流接收到 ticker 列表和日期范围
- **THEN** 19 个分析师通过 LLM 分析数据并返回真实信号
- **AND** Risk Manager 计算波动率和仓位限制
- **AND** Portfolio Manager 综合信号生成 buy/sell/hold 决策
- **AND** OrderDispatcher 将决策转换为订单请求

### P1：回测引擎与 GUI

#### Requirement: BacktestEngine 真实回测逻辑
`BacktestEngine.run()` SHALL 接受策略和 tickers，通过 `VnpyAdapter` 加载历史数据，调用 `BacktestController` 模拟交易，通过 `metrics.py` 计算绩效指标，返回包含 status、metrics、trades 的完整结果字典。

#### Requirement: VnpyAdapter 数据加载
`VnpyAdapter.load_bars()` SHALL 通过 vnpy 的 `MainEngine` 和 `BaseDatabase.load_bar_data()` 加载历史 BarData，返回 BarData 列表。需正确构造 BarData 查询参数（symbol、exchange、interval、start/end datetime）。

#### Requirement: vnpy GUI AI Agent 菜单
`vnpy/trader/ui/mainwindow.py` SHALL 新增 "AI Agent" 菜单项，包含 "启动 AI 对冲基金"、"配置 Agent"、"信号监控" 子菜单项，触发 `AiHedgeFundApp` 的相应功能。

### P2：工具、LLM 扩展、Web、UI

#### Requirement: tools/ 目录
`vnpy_ai/tools/__init__.py` 和 `vnpy_ai/tools/api.py` SHALL 提供数据获取工具函数，从 `ai-hedge-fund/src/tools/api.py` 移植并适配为通过 `DataAdapter` 获取数据（替代 Financial Datasets API 直接调用）。

#### Requirement: utils/ 目录
`vnpy_ai/utils/` SHALL 包含：
- `analysts.py`：分析师注册表
- `api_key.py`：API Key 管理（从 state 或环境变量读取，脱敏处理）
- `llm.py`：`call_llm()` 封装，支持结构化输出和重试
- `display.py`：控制台显示工具
- `progress.py`：进度跟踪器
- `visualize.py`：可视化工具

#### Requirement: 14 个 LLM Provider
`vnpy_ai/llm/models.py` SHALL 支持 14 个 provider：Alibaba、Anthropic、DeepSeek、Google、Groq、Kimi、Meta、Mistral、OpenAI、Ollama、OpenRouter、GigaChat、Azure OpenAI、xAI。每个 provider 使用对应的 langchain_* 包，导入失败时优雅降级。

#### Requirement: LLM 模型配置 JSON
`vnpy_ai/llm/api_models.json` 和 `vnpy_ai/llm/ollama_models.json` SHALL 从 `ai-hedge-fund/src/llm/` 移植，提供模型列表配置。

#### Requirement: Web 后端 services 真实实现
`vnpy_ai_web/backend/services/` 中的 `graph.py`、`agent_service.py`、`backtest_service.py` SHALL 替换 stub 为真实实现：
- `graph.py`：调用 `vnpy_ai.workflow.graph.build_workflow_graph` 构建工作流
- `agent_service.py`：调用 `vnpy_ai.agents.catalog` 获取 Agent 元数据
- `backtest_service.py`：调用 `vnpy_ai.backtesting.engine.BacktestEngine` 执行回测

#### Requirement: UI 组件真实 PySide6 界面
`vnpy_ai/ui/` 中的 4 个组件 SHALL 替换 stub 为真实 PySide6 界面：
- `setting_widget.py`：Agent 参数配置面板（触发频率、分析师选择、LLM 模型、仓位上限等）
- `analyst_selector.py`：分析师多选组件（QListWidget with checkboxes）
- `model_config_widget.py`：LLM 模型配置面板（provider 下拉、model 名称、temperature）
- `signal_monitor.py`：AI 信号实时监控面板（QTableWidget 显示最近信号和决策）

### P3：非阻塞项

#### Requirement: add_ai_agent() 方法
`vnpy/trader/engine.py` 的 `MainEngine` SHALL 新增 `add_ai_agent(agent_class)` 方法，作为 `add_app()` 的语义化别名，专门用于注册 AI Agent 策略。

#### Requirement: 测试环境目录
SHALL 创建 `C:\Users\DELL\.vntrader\log\` 目录（通过测试 fixture 或 conftest.py 自动创建），确保 `test_engine_integration.py` 可正常运行。

---

## MODIFIED Requirements

### Requirement: AgentBase 数据获取
`AgentBase` 已提供 `get_prices`、`get_financial_metrics`、`get_company_news`、`get_portfolio` 方法。本 spec 不修改基类，但子类的 `analyze()` 方法将实际调用这些方法获取数据并传给 LLM。

### Requirement: WorkflowRunner
`WorkflowRunner` 已支持 LLM 回退路径。本 spec 不修改 runner，但工作流图将使用真实 Agent 节点，runner 调用的 `compiled_graph.invoke()` 将产生真实决策。
