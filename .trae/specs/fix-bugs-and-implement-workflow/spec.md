# Fix Bugs and Implement Core AI Workflow Spec

## Why
当前实现存在 2 个 P0 Bug 阻塞实盘链路，且方案 §5.7-5.8 的 Agent 基类和工作流图完全未实现（0%），导致 AI 决策引擎无法运行。本 spec 修复 Bug 并补齐 Phase 1-2 核心缺失，使 AI 工作流从降级模式升级为完整的 LangGraph 多 Agent 决策链路。

## What Changes
- 修复 2 个 P0 Bug（send_decision 返回值、on_market_event 节流）
- 修复 3 个 P1 问题（事件常量导入、配置路径、降级 confidence）
- 新增 `vnpy_ai/agents/base.py` — Agent 基类，统一数据获取
- 新增 `vnpy_ai/workflow/graph.py` — LangGraph StateGraph 构建
- 新增 `vnpy_ai/workflow/nodes.py` — OrderDispatcher、StatusSync、FallbackHandler 节点
- 新增 `vnpy_ai/llm/models.py` — LLM 模型工厂
- 新增 `vnpy_ai/data/cache.py` — 内存缓存
- 补充测试：event_adapter、engine.workflow、agent_base、order flow

## Impact
- Affected specs: 无（新 spec）
- Affected code: `vnpy_ai/engine.py`, `vnpy_ai/order_adapter.py`, `vnpy_ai/event_adapter.py`, `vnpy_ai/config.py`, `vnpy_ai/workflow/runner.py`, `vnpy_ai/agents/`, `vnpy_ai/workflow/`, `vnpy_ai/llm/`, `vnpy_ai/data/`, `tests/`

---

## ADDED Requirements

### Requirement: P0 Bug — send_decision 返回值修复
OrderAdapter.send_decision() SHALL 返回 `list[str]` 或取第一个 vt_orderid，而非 `str(list)`。

#### Scenario: 单笔订单发送
- **WHEN** main_engine.send_order 返回 `["CTP.1-1"]`
- **THEN** send_decision 返回 `"CTP.1-1"`（字符串，非 `"['CTP.1-1']"`）

#### Scenario: 空列表（下单失败）
- **WHEN** main_engine.send_order 返回 `[]`
- **THEN** send_decision 返回 `""`（空字符串）

### Requirement: P0 Bug — on_market_event 节流与 daily 支持
AiHedgeFundEngine.on_market_event() SHALL 支持 daily 频率触发，并对 tick/bar 频率添加最小间隔节流。

#### Scenario: daily 频率首次触发
- **WHEN** trigger_frequency="daily" 且当天首次市场事件到达
- **THEN** 触发 run_workflow，并记录当天日期

#### Scenario: daily 频率同一天内不重复触发
- **WHEN** trigger_frequency="daily" 且当天已触发过
- **THEN** 跳过，不触发 run_workflow

#### Scenario: tick 频率有最小间隔
- **WHEN** trigger_frequency="tick" 且距离上次触发不足 signal_cooldown 秒
- **THEN** 跳过，不触发 run_workflow

### Requirement: P1 — 事件常量从 vnpy.trader.event 导入
EventAdapter SHALL 从 `vnpy.trader.event` 导入 EVENT_AI_* 常量，不再重复定义。

#### Scenario: 事件常量一致性
- **WHEN** 修改 vnpy/trader/event.py 中的事件常量值
- **THEN** EventAdapter 自动使用新值，无需手动同步

### Requirement: P1 — 配置路径基于 __file__
DEFAULT_CONFIG_PATH SHALL 基于 `__file__` 计算绝对路径，而非依赖 CWD。

#### Scenario: 从任意目录运行
- **WHEN** 从 `/tmp` 目录运行 `python -c "from vnpy_ai.config import DEFAULT_CONFIG_PATH"`
- **THEN** DEFAULT_CONFIG_PATH 指向正确的 config 目录

### Requirement: P1 — 降级决策 confidence 改为 0
WorkflowRunner 降级模式下 SHALL 设置 confidence=0，以区分 AI 决策和降级兜底。

#### Scenario: 降级决策
- **WHEN** LLM 不可用，工作流进入降级模式
- **THEN** 返回的 DecisionResult.confidence 为 0

### Requirement: Agent 基类
vnpy_ai/agents/base.py SHALL 提供 AgentBase 类，封装统一的数据获取逻辑（get_prices、get_financial_metrics、get_company_news、get_portfolio）。

#### Scenario: Agent 获取价格数据
- **WHEN** Agent 调用 self.get_prices("AAPL", "2024-01-01", "2024-12-31")
- **THEN** 通过 DataAdapter 获取价格数据并返回 Price 列表

#### Scenario: Agent 获取财务指标
- **WHEN** Agent 调用 self.get_financial_metrics("AAPL")
- **THEN** 返回 FinancialMetrics 模型（数据缺失时返回空列表）

### Requirement: LangGraph 工作流图
vnpy_ai/workflow/graph.py SHALL 构建 LangGraph StateGraph，包含：Start → 分析师 Agent 并行 → Risk Manager → Portfolio Manager → OrderDispatcher → End。

#### Scenario: 完整工作流执行
- **WHEN** 调用 graph.invoke(initial_state)
- **THEN** 按拓扑顺序执行各节点，最终返回包含 decisions 的最终状态

#### Scenario: LLM 不可用时降级
- **WHEN** 工作流中 LLM 调用失败
- **THEN** FallbackHandler 节点接管，返回 hold 决策

### Requirement: 工作流节点
vnpy_ai/workflow/nodes.py SHALL 实现 OrderDispatcher、StatusSync、FallbackHandler 三个节点。

#### Scenario: OrderDispatcher 处理决策
- **WHEN** Portfolio Manager 输出 buy AAPL 决策
- **THEN** OrderDispatcher 调用 OrderAdapter 发送订单

#### Scenario: StatusSync 推送状态
- **WHEN** 工作流执行到 StatusSync 节点
- **THEN** 通过 RPC 向 vnpy 主进程推送当前工作流状态

#### Scenario: FallbackHandler 降级
- **WHEN** LLM 调用失败触发 FallbackHandler
- **THEN** 返回 hold 决策，confidence=0

### Requirement: LLM 模型工厂
vnpy_ai/llm/models.py SHALL 从 `ai-hedge-fund/src/llm/` 移植 LLM 模型工厂代码，支持多提供商模型创建。

#### Scenario: 创建 OpenAI 模型
- **WHEN** 配置 llm_provider="OpenAI", llm_model_name="gpt-4.1"
- **THEN** create_model() 返回 LangChain ChatOpenAI 实例

#### Scenario: LLM 不可用
- **WHEN** 本机无 langchain 依赖
- **THEN** create_model() 返回 None，不抛异常

### Requirement: 内存缓存
vnpy_ai/data/cache.py SHALL 提供内存缓存，支持 TTL 配置，缓存价格和财务数据。

#### Scenario: 缓存命中
- **WHEN** 请求已在缓存中且未过期的数据
- **THEN** 直接返回缓存数据，不调用 DataAdapter

#### Scenario: 缓存过期
- **WHEN** 请求的缓存数据已超过 TTL
- **THEN** 重新调用 DataAdapter 获取数据并更新缓存

### Requirement: 测试补充
SHALL 新增 test_event_adapter.py、test_engine_workflow.py、test_agent_base.py、test_order_flow.py，覆盖事件发布、工作流降级路径、Agent 基类、端到端订单流。

#### Scenario: 事件适配器测试
- **WHEN** 运行 pytest tests/unit/test_event_adapter.py
- **THEN** 所有测试通过，覆盖 EVENT_AI_SIGNAL/EVENT_AI_DECISION/EVENT_AI_ERROR/EVENT_AI_STATUS 发布

#### Scenario: 工作流降级测试
- **WHEN** 运行 pytest tests/unit/test_engine_workflow.py
- **THEN** 验证 LLM 不可用时返回 hold 决策（confidence=0）

---

## MODIFIED Requirements

### Requirement: WorkflowRunner 降级逻辑
WorkflowRunner.run() 降级时 SHALL 设置 confidence=0，并记录 reasoning 为 "LLM unavailable; fallback to hold"。

### Requirement: EventAdapter 事件常量来源
EventAdapter SHALL 从 `vnpy.trader.event` 导入事件常量，移除本地重复定义。

### Requirement: config.py 路径计算
DEFAULT_CONFIG_PATH SHALL 使用 `Path(__file__).resolve().parent.parent / "config" / "default_settings.json"`。

### Requirement: OrderAdapter.send_decision 返回值
SHALL 返回 `vt_orderids[0] if vt_orderids else ""`，而非 `str(list)`。

### Requirement: AiHedgeFundEngine.on_market_event 触发逻辑
SHALL 支持 daily 频率，SHALL 对 tick 频率添加 signal_cooldown 秒最小间隔。