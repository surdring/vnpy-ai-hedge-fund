# Complete All Remaining Items Spec

## Why
审查报告识别出 53 项仍待实现的功能，分布在 P2（核心引擎/RPC/数据/订单/Agent/Web 后端）和 P3（回测/GUI/运维/文档/测试）两个优先级。本 spec 覆盖全部 53 项，按类别分组实现，优先 P2 后 P3。

## What Changes
- 类别一：核心引擎增强（3 项）— signal_cooldown 配置、sma_cross 降级策略、进度报告
- 类别二：RPC 通信增强（3 项）— 断线重连、心跳、离线缓冲
- 类别三：数据适配增强（6 项）— financial_metrics、company_news、portfolio 完善、datafeed 接口、日期校验、缓存集成
- 类别四：订单适配增强（3 项）— 仓位资金校验、价格范围校验、订单状态 RPC 回调
- 类别五：Agent 工作流完善（3 项）— 19 个分析师移植、AiSignalData/AiDecisionData 转换、错误处理协议
- 类别六：Web 后端（7 项）— /backtest、/flows、database、alembic、repositories、services、routes
- 类别七：回测引擎（10 项）— engine、controller、trader、metrics、portfolio、valuation、output、benchmarks、types、vnpy_adapter
- 类别八：桌面 GUI（4 项）— setting_widget、analyst_selector、model_config_widget、signal_monitor
- 类别九：运维与部署（5 项）— Dockerfile 完善、健康检查、日志聚合、Prometheus、通知集成
- 类别十：文档与工程（5 项）— api_reference、migration_guide、notebook、CHANGELOG、LICENSE
- 类别十一：测试（4 项）— Playwright、fixtures、mypy、docker compose config

## Impact
- Affected specs: 无（新 spec）
- Affected code: `vnpy_ai/engine.py`, `vnpy_ai/data_adapter.py`, `vnpy_ai/order_adapter.py`, `vnpy_ai/rpc_bridge.py`, `vnpy_ai/event_adapter.py`, `vnpy_ai/agents/`, `vnpy_ai/workflow/`, `vnpy_ai/llm/`, `vnpy_ai/backtesting/`（新建）, `vnpy_ai/ui/`（新建）, `vnpy_ai_web/backend/`, `docker/`, `docs/`, `tests/`, `config/`

---

## ADDED Requirements

### 类别一：核心引擎增强

#### Requirement: signal_cooldown 独立可配置项
AiHedgeFundEngine SHALL 将 signal_cooldown 作为 `settings` 中的独立可配置项，默认值 60 秒，并在 `on_market_event` 中生效。

#### Requirement: sma_cross 降级策略
WorkflowRunner SHALL 支持 `sma_cross` 降级策略：当 LLM 不可用时，计算短期/长期 SMA 交叉信号，金叉买、死叉卖，否则 hold。

#### Requirement: 进度报告到 UI
WorkflowRunner SHALL 在执行过程中通过 EventAdapter 发布 EVENT_AI_STATUS 事件，携带 `start`/`progress`/`complete` 状态和进度百分比。

### 类别二：RPC 通信增强

#### Requirement: 断线重连 + 指数退避
RpcBridge SHALL 支持断线自动重连，使用 1s/2s/4s/8s 指数退避，最大重试 5 次后放弃并通知主进程。

#### Requirement: 心跳机制
RpcBridge SHALL 支持可配置间隔（默认 10 秒）的心跳，连续 3 次未收到心跳视为断开，触发重连。

#### Requirement: 离线消息缓冲
RpcBridge SHALL 在断线期间缓存待发送消息（最多 1000 条），恢复连接后按序重放。

### 类别三：数据适配增强

#### Requirement: get_financial_metrics 实现
DataAdapter.get_financial_metrics() SHALL 返回 FinancialMetrics Pydantic 模型列表，数据缺失时返回空列表。

#### Requirement: get_company_news 实现
DataAdapter.get_company_news() SHALL 返回新闻条目列表，支持从 vnpy datafeed 获取。

#### Requirement: get_portfolio 完善
DataAdapter.get_portfolio() SHALL 返回包含 positions、account 资金信息、总权益的完整 Portfolio 模型。

#### Requirement: datafeed 扩展接口
DataAdapter SHALL 保留 `_datafeed` 属性作为可选扩展点，财务指标/新闻/内部交易均可通过 datafeed 获取。

#### Requirement: get_prices 日期格式校验
DataAdapter.get_prices() SHALL 对 start_date/end_date 参数做 try/except 保护，格式错误时使用默认值。

#### Requirement: 缓存集成到 DataAdapter
DataAdapter SHALL 集成 Cache 类，get_prices/get_financial_metrics 结果缓存，TTL 可配置（默认 300 秒）。

### 类别四：订单适配增强

#### Requirement: 仓位与资金校验
OrderAdapter SHALL 在下单前检查当前持仓（不允许超卖）和可用资金（不允许超买），校验失败时返回空字符串并记录日志。

#### Requirement: 价格范围校验
OrderAdapter SHALL 对比最新市场价，若委托价格偏离超过 5% 则拒绝下单并记录警告。

#### Requirement: 订单状态回调到 RPC
OrderAdapter SHALL 监听 vnpy 的 EVENT_ORDER/EVENT_TRADE 事件，状态变更时通过 RpcBridge 回传 Agent 进程。

### 类别五：Agent 工作流完善

#### Requirement: 19 个分析师 Agent 移植
从 `ai-hedge-fund/src/agents/` 移植 19 个分析师 Agent 到 `vnpy_ai/agents/`，继承 AgentBase，保留原始作者信息。

#### Requirement: AiSignalData/AiDecisionData 转换
EventAdapter SHALL 将 WorkflowResult 中的 DecisionResult 转换为 AiSignalData/AiDecisionData dataclass 后发布事件。

#### Requirement: 错误处理协议
RPC 消息 SHALL 包含统一错误码字段（`error_code` + `error_message`），发送方实现自动重试（最多 3 次）。

### 类别六：Web 后端

#### Requirement: /hedge-fund/backtest 端点
Web 后端 SHALL 提供 `/hedge-fund/backtest` POST 端点，接收回测参数并返回 SSE 流式进度。

#### Requirement: /flows CRUD 端点
Web 后端 SHALL 提供 `/flows` 的 GET/POST/PUT/DELETE 端点，支持工作流拓扑的持久化。

#### Requirement: database 数据层
Web 后端 SHALL 包含 `backend/database/models.py`（SQLAlchemy ORM）和 `backend/database/session.py`。

#### Requirement: alembic 数据库迁移
Web 后端 SHALL 包含 `backend/alembic/` 完整迁移链，支持自动生成和升级。

#### Requirement: repositories 数据仓库
Web 后端 SHALL 包含 `api_key_repository.py`、`flow_repository.py`、`flow_run_repository.py`。

#### Requirement: services 服务层
Web 后端 SHALL 包含 `agent_service.py`、`backtest_service.py`、`ollama_service.py`、`graph.py`、`portfolio.py`。

#### Requirement: routes 完整路由
Web 后端 SHALL 包含 `api_keys.py`、`flow_runs.py`、`flows.py`、`hedge_fund.py`、`language_models.py`、`ollama.py`、`storage.py`。

### 类别七：回测引擎

#### Requirement: 回测引擎主入口
`vnpy_ai/backtesting/engine.py` SHALL 提供统一回测入口，接受配置和策略参数，返回绩效结果。

#### Requirement: 回测控制器
`vnpy_ai/backtesting/controller.py` SHALL 管理资金、滑点、手续费、每日结算。

#### Requirement: 回测交易模拟器
`vnpy_ai/backtesting/trader.py` SHALL 模拟订单执行，支持市价/限价成交逻辑。

#### Requirement: 绩效指标
`vnpy_ai/backtesting/metrics.py` SHALL 计算夏普比率、Sortino 比率、最大回撤、年化收益、胜率。

#### Requirement: 投资组合状态跟踪
`vnpy_ai/backtesting/portfolio.py` SHALL 跟踪每日持仓、现金、总权益变化。

#### Requirement: 估值计算
`vnpy_ai/backtesting/valuation.py` SHALL 计算组合估值和持仓市值。

#### Requirement: 回测结果输出
`vnpy_ai/backtesting/output.py` SHALL 支持 CSV 导出、HTML 报告、matplotlib 图表。

#### Requirement: 基准对比
`vnpy_ai/backtesting/benchmarks.py` SHALL 支持与基准指数（如 SPY）对比。

#### Requirement: 回测类型定义
`vnpy_ai/backtesting/types.py` SHALL 定义回测相关的 Pydantic 模型和类型。

#### Requirement: vnpy 适配器
`vnpy_ai/backtesting/vnpy_adapter.py` SHALL 作为 vnpy 回测框架与 AI 回测引擎的桥接层。

### 类别八：桌面 GUI

#### Requirement: setting_widget.py
`vnpy_ai/ui/setting_widget.py` SHALL 提供 Agent 参数配置面板（PySide6）。

#### Requirement: analyst_selector.py
`vnpy_ai/ui/analyst_selector.py` SHALL 提供分析师多选/拖拽选择组件。

#### Requirement: model_config_widget.py
`vnpy_ai/ui/model_config_widget.py` SHALL 提供 LLM 模型配置面板（provider、model_name、temperature）。

#### Requirement: signal_monitor.py
`vnpy_ai/ui/signal_monitor.py` SHALL 提供 AI 信号实时监控面板，展示最近信号和决策。

### 类别九：运维与部署

#### Requirement: Dockerfile 完善
`docker/Dockerfile.core`、`docker/Dockerfile.agent`、`docker/Dockerfile.web` SHALL 补充完整的依赖安装步骤。

#### Requirement: 健康检查端点
Web 后端 SHALL 提供 `/health` 端点，返回 200 和 `{"status": "ok"}`。

#### Requirement: 日志聚合
所有进程 SHALL 输出 stdout JSON 格式日志，支持外部日志收集系统。

#### Requirement: Prometheus 指标暴露
新增 `/metrics` 端点，暴露交易延迟、Agent 处理时间、内存使用等指标。

#### Requirement: 通知集成
AiHedgeFundEngine SHALL 支持通过邮件/微信推送 Agent 决策结果。

### 类别十：文档与工程

#### Requirement: docs/api_reference.md
SHALL 创建 API 参考文档，覆盖所有公开接口。

#### Requirement: docs/migration_guide.md
SHALL 创建迁移指南，说明从独立 AI HF 到 vnpy 集成的迁移步骤。

#### Requirement: examples/notebook/ai_agent_research.ipynb
SHALL 创建 Jupyter Notebook 投研示例。

#### Requirement: CHANGELOG.md
SHALL 创建变更日志文件。

#### Requirement: LICENSE
SHALL 创建项目许可证文件。

### 类别十一：测试

#### Requirement: Playwright 前端冒烟测试
SHALL 创建 Playwright 脚本，验证关键页面（工作流编辑器、回测结果）可正常渲染。

#### Requirement: tests/fixtures/ 测试数据
SHALL 创建 `tests/fixtures/mock_agent_outputs.py` 等测试数据文件。

#### Requirement: mypy 类型检查
SHALL 安装 mypy 并执行 `mypy vnpy_ai/`，修复类型错误。

#### Requirement: docker compose config 验证
SHALL 安装 Docker CLI 并执行 `docker compose config` 验证配置正确性。