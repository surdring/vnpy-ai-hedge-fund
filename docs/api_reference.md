# API Reference

## DataAdapter（数据适配器）

`vnpy_ai.data_adapter`

将 VeighNa 数据对象转换为 AI Hedge Fund 兼容的数据模型。

### 模块级函数

| 函数 | 说明 |
|------|------|
| `parse_vt_symbol(vt_symbol, default_exchange)` | 解析 `symbol.EXCHANGE` 格式的 vt_symbol 为 (symbol, exchange) 元组 |
| `bar_to_price(bar)` | 将 VeighNa `BarData` 转换为 `Price` 模型 |
| `tick_to_price(tick)` | 将 VeighNa `TickData` 转换为 `Price` 模型 |

### DataAdapter 类

```python
from vnpy_ai.data_adapter import DataAdapter

adapter = DataAdapter(main_engine)
```

| 方法 | 说明 |
|------|------|
| `__init__(main_engine)` | 初始化，接收 VeighNa MainEngine 实例 |
| `get_prices(ticker, start_date, end_date) -> list[Price]` | 从 VeighNa 数据库加载日线 OHLCV 数据 |
| `get_latest_price(ticker) -> Price \| None` | 获取内存中最新 Tick 快照 |
| `get_portfolio(tickers=None) -> dict` | 将 VeighNa 账户和持仓状态转换为 AI HF 组合格式 |
| `get_financial_metrics(ticker, end_date, period, limit) -> list[FinancialMetrics]` | 获取财务指标（预留接口，当前返回空列表） |
| `get_company_news(ticker, end_date, start_date, limit) -> list[CompanyNews]` | 获取公司新闻（预留接口，当前返回空列表） |
| `get_insider_trades(ticker, end_date, start_date, limit) -> list[InsiderTrade]` | 获取内部交易（预留接口，当前返回空列表） |

### 使用示例

```python
from vnpy_ai.data_adapter import DataAdapter

adapter = DataAdapter(main_engine)

# 获取历史价格
prices = adapter.get_prices("AAPL.SMART", "2024-01-01", "2024-12-31")
for p in prices:
    print(f"{p.time}: O={p.open} H={p.high} L={p.low} C={p.close} V={p.volume}")

# 获取最新价格
latest = adapter.get_latest_price("AAPL.SMART")
if latest:
    print(f"最新价: {latest.close}")

# 获取组合状态
portfolio = adapter.get_portfolio(["AAPL.SMART", "GOOGL.SMART"])
print(f"现金: {portfolio['cash']}")
```

---

## OrderAdapter（订单适配器）

`vnpy_ai.order_adapter`

将 AI 决策转换为 VeighNa `OrderRequest` 对象并提交。

### 数据类

| 类 | 说明 |
|------|------|
| `OrderValidationResult(ok, reason)` | 订单验证结果，`ok` 为布尔值，`reason` 为错误原因 |

### OrderAdapter 类

```python
from vnpy_ai.order_adapter import OrderAdapter

adapter = OrderAdapter(main_engine, gateway_name="CTP", order_type=OrderType.LIMIT)
```

| 方法 | 说明 |
|------|------|
| `__init__(main_engine, gateway_name, order_type)` | 初始化，绑定主引擎和网关 |
| `validate_decision(decision) -> OrderValidationResult` | 验证 AI 决策（检查 action、quantity、price、合约限制） |
| `decision_to_order(decision) -> OrderRequest \| None` | 将 `PortfolioDecision` 转换为 `OrderRequest`（hold 返回 None） |
| `send_decision(decision) -> str` | 转换并提交订单到 MainEngine，返回 vt_orderid |

### 支持的 Action 映射

| Action | Direction | Offset |
|--------|-----------|--------|
| `buy` | LONG | OPEN |
| `sell` | LONG | CLOSE |
| `short` | SHORT | OPEN |
| `cover` | SHORT | CLOSE |
| `hold` | — | 不产生订单 |

### 使用示例

```python
from vnpy_ai.order_adapter import OrderAdapter
from vnpy_ai.models import PortfolioDecision

adapter = OrderAdapter(main_engine, gateway_name="CTP")

decision = PortfolioDecision(
    ticker="AAPL.SMART",
    action="buy",
    quantity=100,
    confidence=0.85,
    reasoning="技术面看涨",
)

validation = adapter.validate_decision(decision)
if validation.ok:
    order_id = adapter.send_decision(decision)
    print(f"订单已提交: {order_id}")
else:
    print(f"验证失败: {validation.reason}")
```

---

## EventAdapter（事件适配器）

`vnpy_ai.event_adapter`

将 AI 工作流输出发布到 VeighNa EventEngine。

### EventAdapter 类

```python
from vnpy_ai.event_adapter import EventAdapter

adapter = EventAdapter(event_engine)
```

| 方法 | 说明 |
|------|------|
| `__init__(event_engine)` | 初始化，绑定 VeighNa EventEngine |
| `publish_signal(signal)` | 发布 `AnalystSignal` 事件（`EVENT_AI_SIGNAL`） |
| `publish_decision(decision)` | 发布 `PortfolioDecision` 事件（`EVENT_AI_DECISION`） |
| `publish_order_decision(payload)` | 发布下单决策事件（`EVENT_AI_DECISION_ORDER`） |
| `publish_error(message, agent)` | 发布错误事件并记录日志（`EVENT_AI_ERROR`） |
| `publish_status(status, agent, progress)` | 发布状态更新事件（`EVENT_AI_STATUS`） |
| `publish_workflow_result(result)` | 批量发布工作流结果中的所有决策 |

### 事件常量

| 常量 | 事件值 | 说明 |
|------|--------|------|
| `EVENT_AI_SIGNAL` | `"eAiSignal"` | 分析师信号 |
| `EVENT_AI_DECISION` | `"eAiDecision"` | 投资决策 |
| `EVENT_AI_DECISION_ORDER` | `"eAiDecisionOrder"` | 下单决策 |
| `EVENT_AI_ERROR` | `"eAiError"` | AI 错误 |
| `EVENT_AI_STATUS` | `"eAiStatus"` | AI 状态 |

### 使用示例

```python
from vnpy_ai.event_adapter import EventAdapter, EVENT_AI_SIGNAL

adapter = EventAdapter(event_engine)

# 监听 AI 信号
def on_ai_signal(event):
    signal = event.data
    print(f"{signal.agent_name} 对 {signal.ticker} 发出 {signal.signal} 信号")

event_engine.register(EVENT_AI_SIGNAL, on_ai_signal)
```

---

## RpcBridge（RPC 桥接）

`vnpy_ai.rpc_bridge`

提供 VeighNa 主进程与 AI Agent 子进程之间的 RPC 通信。

### 模块级函数

| 函数 | 说明 |
|------|------|
| `make_address(host, port) -> str` | 生成 TCP ZMQ 地址（格式 `tcp://host:port`） |
| `rpc_message(message_type, payload) -> dict` | 构建 JSON 可序列化的 RPC 消息 |

### 数据类

| 类 | 说明 |
|------|------|
| `RpcAddresses(rep, pub)` | RPC 地址对（REP 和 PUB 地址） |

### 消息类型常量

| 常量 | 说明 |
|------|------|
| `REQUEST_MARKET_DATA` | 请求市场数据 |
| `RESPONSE_MARKET_DATA` | 市场数据响应 |
| `REQUEST_PORTFOLIO` | 请求组合数据 |
| `RESPONSE_PORTFOLIO` | 组合数据响应 |
| `SUBMIT_ORDER` | 提交订单 |
| `ORDER_STATUS` | 订单状态 |
| `AGENT_SIGNAL` | 代理信号 |
| `HEARTBEAT` | 心跳 |

### AiRpcServer 类

```python
from vnpy_ai.rpc_bridge import AiRpcServer

server = AiRpcServer()
```

| 方法 | 说明 |
|------|------|
| `__init__()` | 初始化 RPC 服务端 |
| `register(func)` | 注册可调用的 RPC 函数 |
| `start(rep_address, pub_address)` | 启动 RPC 服务端 |
| `stop()` | 停止并等待服务端退出 |
| `publish(message_type, payload)` | 发布消息到所有订阅者 |

### AiRpcClient 类

```python
from vnpy_ai.rpc_bridge import AiRpcClient

client = AiRpcClient()
```

| 属性 | 说明 |
|------|------|
| `messages: list[RpcMessage]` | 存储接收到的消息 |
| `connected: bool` | 连接状态 |

| 方法 | 说明 |
|------|------|
| `callback(topic, data)` | 接收消息回调，解析并存储为 `RpcMessage` |
| `on_disconnected()` | 断开连接回调 |

### 使用示例

```python
from vnpy_ai.rpc_bridge import AiRpcServer, make_address

server = AiRpcServer()

@server.register
def get_market_data(ticker: str):
    return {"ticker": ticker, "price": 150.0}

server.start(
    rep_address=make_address("127.0.0.1", 9001),
    pub_address=make_address("127.0.0.1", 9002),
)
```

---

## WorkflowRunner（工作流运行器）

`vnpy_ai.workflow.runner`

运行 AI 工作流，支持 LangGraph 编译图执行和降级 fallback 路径。

### 模块级函数

| 函数 | 说明 |
|------|------|
| `create_initial_state(tickers, portfolio, start_date, end_date, model_name, model_provider) -> AgentState` | 创建 AI Hedge Fund 兼容的工作流初始状态 |
| `get_agents_list() -> list[dict]` | 返回分析师元数据，供 Web/UI 选择器使用 |

### WorkflowRunner 类

```python
from vnpy_ai.workflow.runner import WorkflowRunner

runner = WorkflowRunner(data_adapter, selected_analysts=["warren_buffett", "technical_analyst"])
```

| 方法 | 说明 |
|------|------|
| `__init__(data_adapter, selected_analysts)` | 初始化，可选择指定的分析师列表 |
| `run(tickers, portfolio, start_date, end_date, model_name, model_provider) -> WorkflowResult` | 运行工作流，LLM 不可用时自动降级为 hold 策略 |

### 默认分析师列表

默认包含 19 个分析师：`aswath_damodaran`, `ben_graham`, `bill_ackman`, `cathie_wood`, `charlie_munger`, `michael_burry`, `mohnish_pabrai`, `nassim_taleb`, `peter_lynch`, `phil_fisher`, `rakesh_jhunjhunwala`, `stanley_druckenmiller`, `warren_buffett`, `technical_analyst`, `fundamentals_analyst`, `growth_analyst`, `news_sentiment_analyst`, `sentiment_analyst`, `valuation_analyst`

### 使用示例

```python
from vnpy_ai.data_adapter import DataAdapter
from vnpy_ai.workflow.runner import WorkflowRunner

adapter = DataAdapter(main_engine)
runner = WorkflowRunner(adapter)

result = runner.run(
    tickers=["AAPL.SMART"],
    model_name="llama3",
    model_provider="Ollama",
)

for ticker, decision in result.decisions.items():
    print(f"{ticker}: {decision.action} (置信度: {decision.confidence})")
```

---

## AgentBase（Agent 基类）

`vnpy_ai.agents.base`

所有 AI 分析师 Agent 的基类，提供统一的数据获取接口。

### AgentBase 类

```python
from vnpy_ai.agents.base import AgentBase

class MyAnalyst(AgentBase):
    agent_id = "my_analyst"
    agent_name = "我的分析师"

    def analyze(self, state):
        prices = self.get_prices("AAPL", state["data"]["start_date"], state["data"]["end_date"])
        return {"agent_id": self.agent_id, "signal": "bullish", "confidence": 0.8}
```

| 属性 | 说明 |
|------|------|
| `agent_id: str` | Agent 唯一标识（子类需覆盖） |
| `agent_name: str` | Agent 显示名称（子类需覆盖） |

| 方法 | 说明 |
|------|------|
| `__init__(data_adapter)` | 初始化，绑定 DataAdapter |
| `get_prices(ticker, start_date, end_date) -> list[Price]` | 获取历史价格数据 |
| `get_financial_metrics(ticker) -> list[FinancialMetrics]` | 获取财务指标 |
| `get_company_news(ticker) -> list[CompanyNews]` | 获取公司新闻 |
| `get_portfolio() -> dict` | 获取当前组合状态 |
| `analyze(state) -> dict` | 执行分析（子类必须实现），返回包含 agent_id 和分析结果 |

---

## LLM 模型

`vnpy_ai.llm.models`

LLM 模型工厂，支持懒加载，不强制依赖 LangChain。

### 函数

| 函数 | 说明 |
|------|------|
| `create_model(provider, model_name, **kwargs) -> Any` | 创建 LangChain ChatModel 实例，返回 None 如果对应包未安装 |
| `get_available_providers() -> list[str]` | 返回当前环境可用的 LLM 提供商列表 |

### 支持的 Provider

| Provider | 所需包 | 说明 |
|----------|--------|------|
| `openai` / `azure` | `langchain-openai` | OpenAI / Azure OpenAI |
| `anthropic` | `langchain-anthropic` | Anthropic Claude |
| `ollama` | `langchain-ollama` | 本地 Ollama 模型 |
| `google` | `langchain-google-genai` | Google Gemini |

### 使用示例

```python
from vnpy_ai.llm.models import create_model, get_available_providers

# 查看可用 Provider
print(get_available_providers())  # ['ollama', 'openai']

# 创建模型
model = create_model(provider="ollama", model_name="llama3")
if model:
    response = model.invoke("分析 AAPL 股票走势")
    print(response.content)
```

---

## LLM 后处理

`vnpy_ai.llm.postprocess`

AI 输出后处理工具，兼容不同 LLM 的输出格式差异。

### 函数

| 函数 | 说明 |
|------|------|
| `clean_reasoning_text(text, max_chars=4000) -> str` | 移除推理过程标记，清理空白，截断到指定长度 |
| `extract_json_from_response(content) -> dict \| None` | 从 LLM 响应中提取第一个 JSON 对象，支持多种格式 |

### 使用示例

```python
from vnpy_ai.llm.postprocess import extract_json_from_response, clean_reasoning_text

raw = '{"action": "buy", "confidence": 0.85}'
result = extract_json_from_response(raw)
print(result)  # {'action': 'buy', 'confidence': 0.85}
```

---

## Cache（缓存）

`vnpy_ai.data.cache`

线程安全的内存缓存，支持按 Key 设置 TTL。

### Cache 类

```python
from vnpy_ai.data.cache import Cache

cache = Cache(default_ttl=300)  # 默认 5 分钟过期
```

| 方法 | 说明 |
|------|------|
| `__init__(default_ttl=300)` | 初始化，设置默认 TTL（秒） |
| `get(key) -> Any` | 获取缓存值，过期或不存在返回 None |
| `set(key, value, ttl=None)` | 设置缓存值，可选指定 TTL |
| `delete(key)` | 删除指定 Key |
| `clear()` | 清空所有缓存 |
| `cleanup()` | 清理所有过期条目 |
| `__len__()` | 返回当前缓存条目数 |
| `__contains__(key)` | 检查 Key 是否存在且未过期 |

### 使用示例

```python
from vnpy_ai.data.cache import Cache

cache = Cache(default_ttl=60)

cache.set("prices:AAPL", [{"close": 150.0, "time": "2024-01-01"}])
data = cache.get("prices:AAPL")  # 60 秒内有效

if "prices:AAPL" in cache:
    print("缓存命中")
```

---

## 数据模型

`vnpy_ai.models`

Pydantic 数据模型，定义 AI Hedge Fund 集成的数据结构。

| 模型 | 说明 |
|------|------|
| `Price` | OHLCV 价格模型（open, close, high, low, volume, time） |
| `FinancialMetrics` | 财务指标模型（ticker, market_cap, pe_ratio 等） |
| `CompanyNews` | 公司新闻模型（ticker, title, source, date, sentiment） |
| `InsiderTrade` | 内部交易模型（ticker, filing_date, transaction_shares 等） |
| `AnalystSignal` | 分析师信号（agent_name, ticker, signal, confidence, reasoning） |
| `PortfolioDecision` | 投资决策（ticker, action, quantity, confidence, reasoning, price） |
| `WorkflowResult` | 工作流结果（decisions, analyst_signals, current_prices, degraded） |
| `RpcMessage` | RPC 消息封装（type, payload, request_id, timestamp） |
| `AgentStatus` | AI 引擎运行时状态（enabled, auto_trading, rpc_connected 等） |
| `AiAction` | 动作类型字面量：`"buy" \| "sell" \| "short" \| "cover" \| "hold"` |

### 工具函数

| 函数 | 说明 |
|------|------|
| `mask_secret(value) -> str \| None` | 脱敏密钥（保留前 3 位和后 4 位，中间 `****`） |

---

## AiHedgeFundEngine（AI 引擎）

`vnpy_ai.engine`

VeighNa 交易引擎，协调数据、事件、工作流执行和订单提交。

### AiHedgeFundEngine 类

```python
from vnpy_ai.engine import AiHedgeFundEngine

engine = AiHedgeFundEngine(main_engine, event_engine)
```

| 属性 | 说明 |
|------|------|
| `settings: AiSettings` | 当前运行时配置 |
| `data_adapter: DataAdapter` | 数据适配器 |
| `event_adapter: EventAdapter` | 事件适配器 |
| `order_adapter: OrderAdapter` | 订单适配器 |
| `workflow_runner: WorkflowRunner` | 工作流运行器 |
| `status: AgentStatus` | AI 引擎状态 |

| 方法 | 说明 |
|------|------|
| `__init__(main_engine, event_engine)` | 初始化引擎，注册事件监听 |
| `register_event()` | 注册 `EVENT_TICK` 和 `EVENT_BAR` 市场数据触发器 |
| `set_config(settings)` | 更新运行时配置（支持 `AiSettings` 或 dict） |
| `get_status() -> AgentStatus` | 获取当前运行时状态 |
| `start_agent_process() -> bool` | 启用 Agent 进程 |
| `stop_agent_process()` | 停用 Agent 进程 |
| `sync_portfolio(tickers=None) -> dict` | 从 VeighNa 同步组合状态 |
| `run_workflow(tickers, start_date, end_date) -> WorkflowResult` | 执行一次 AI 决策周期 |
| `submit_decision(decision) -> str` | 提交或发布投资决策 |
| `on_market_event(event)` | 处理市场数据触发（支持 daily/tick/bar 频率） |
| `close()` | 清理引擎资源 |

---

## AiHedgeFundApp（应用入口）

`vnpy_ai.app`

VeighNa App 注册入口。

### AiHedgeFundApp 类

```python
from vnpy_ai.app import AiHedgeFundApp
```

| 属性 | 值 |
|------|-----|
| `app_name` | `"AiHedgeFund"` |
| `display_name` | `"AI Hedge Fund"` |
| `engine_class` | `AiHedgeFundEngine` |
| `widget_name` | `"AiHedgeFundWidget"` |

---

## 配置加载

`vnpy_ai.config`

| 函数 | 说明 |
|------|------|
| `load_settings(path=None) -> AiSettings` | 从 JSON 文件和环境变量加载配置 |
| `mask_api_keys(api_keys) -> dict` | 脱敏 API Key 字典 |

### AiSettings 配置项

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enabled` | `bool` | `False` | 是否启用 AI 功能 |
| `enable_auto_trading` | `bool` | `False` | 是否启用自动交易 |
| `trigger_frequency` | `str` | `"daily"` | 触发频率（daily / tick / bar） |
| `selected_analysts` | `list[str]` | `[]` | 选择的分析师列表 |
| `llm_model_name` | `str` | `"llama3"` | LLM 模型名称 |
| `llm_provider` | `str` | `"Ollama"` | LLM 提供商 |
| `max_position_ratio` | `float` | `0.2` | 最大持仓比例 |
| `signal_cooldown` | `int` | `300` | 信号冷却时间（秒） |
| `fallback_strategy` | `str` | `"hold"` | 降级策略 |
| `rpc_host` | `str` | `"127.0.0.1"` | RPC 主机地址 |
| `rpc_server_port` | `int` | `9001` | RPC 服务端端口 |
| `rpc_agent_port` | `int` | `9002` | RPC Agent 端口 |
| `gateway_name` | `str` | `""` | 网关名称 |
| `order_type` | `str` | `"LIMIT"` | 订单类型 |

---

## 监控工具

`vnpy_ai.monitoring`

| 函数 | 说明 |
|------|------|
| `is_port_open(host, port, timeout=0.2) -> bool` | 检查本地 TCP 端口是否可达 |
| `read_pid_file(path) -> int \| None` | 读取 PID 文件 |

---

## Workflow Graph（工作流图）

`vnpy_ai.workflow.graph`

| 函数 | 说明 |
|------|------|
| `build_workflow_graph(agents, order_adapter, rpc_bridge) -> Any` | 构建 LangGraph StateGraph，拓扑：Start → Analysts → Risk Manager → Portfolio Manager → OrderDispatcher → StatusSync → End。如果 langgraph 未安装返回 None |

---

## Workflow Nodes（工作流节点）

`vnpy_ai.workflow.nodes`

| 函数 | 说明 |
|------|------|
| `order_dispatcher(state, order_adapter) -> dict` | 将 Portfolio Manager 决策通过 OrderAdapter 转换为订单 |
| `status_sync(state, rpc_bridge) -> dict` | 通过 RPC 推送工作流状态到 VeighNa 主进程 |
| `fallback_handler(state) -> dict` | LLM 不可用时的降级处理，生成 hold 决策 |

---

## Agent Catalog（Agent 目录）

`vnpy_ai.agents.catalog`

| 常量 | 说明 |
|------|------|
| `ANALYST_ORDER` | 分析师元组列表 `(display_name, key)`，共 19 个分析师 |

| 函数 | 说明 |
|------|------|
| `get_agents_list() -> list[dict]` | 返回分析师元数据，包含 key、display_name、description、investing_style、order |