# Migration Guide: 独立 AI Hedge Fund 迁移至 vnpy 整合平台

本指南帮助你将独立的 [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund) 项目迁移到 VeighNa 交易平台中运行，获得实时行情、实盘交易、风控管理等企业级能力。

## 前置条件

- **Python 3.11+**（推荐 3.13）
- **VeighNa** 已安装并配置（`pip install vnpy`）
- 已安装至少一个 VeighNa 交易网关（如 CTP、CTPTEST 等）
- （可选）**LangChain** 和相关 LLM 包（如需使用 AI 分析功能）

## 步骤 1：安装 vnpy_ai 包

```bash
# 克隆整合仓库
git clone <repository-url> vnpy-ai-hedge-fund
cd vnpy-ai-hedge-fund

# 安装核心依赖
pip install -e .

# 安装可选 AI 依赖（如需使用 LangGraph 工作流）
pip install langchain-core langchain-openai langgraph

# 安装本地 LLM 支持（推荐）
pip install langchain-ollama
```

## 步骤 2：配置 settings.json

在 `config/` 目录下创建或编辑 `default_settings.json`：

```json
{
    "enabled": true,
    "enable_auto_trading": false,
    "trigger_frequency": "daily",
    "selected_analysts": [
        "warren_buffett",
        "technical_analyst",
        "sentiment_analyst"
    ],
    "llm_model_name": "llama3",
    "llm_provider": "Ollama",
    "max_position_ratio": 0.2,
    "signal_cooldown": 300,
    "fallback_strategy": "hold",
    "rpc_host": "127.0.0.1",
    "rpc_server_port": 9001,
    "rpc_agent_port": 9002,
    "gateway_name": "CTP",
    "order_type": "LIMIT"
}
```

### 配置项说明

| 配置项 | 说明 |
|--------|------|
| `enabled` | 是否启用 AI 功能（建议先设为 `true`，`enable_auto_trading` 保持 `false` 进行测试） |
| `trigger_frequency` | 触发频率：`"daily"`（每日一次）、`"tick"`（每 Tick）、`"bar"`（每根 K 线） |
| `selected_analysts` | 选择的分析师列表，空列表使用全部 19 个分析师 |
| `llm_model_name` | LLM 模型名称（如 `llama3`、`gpt-4.1`、`claude-3-opus`） |
| `llm_provider` | LLM 提供商：`Ollama`、`OpenAI`、`Anthropic`、`Google` |
| `gateway_name` | VeighNa 交易网关名称 |

### 环境变量配置（可选）

你也可以通过环境变量覆盖配置：

```bash
export AI_AGENT_ENABLED=true
export AI_AGENT_AUTO_TRADE=false
export AI_AGENT_TRIGGER_FREQUENCY=daily
export AI_AGENT_MODEL_NAME=llama3
export AI_AGENT_MODEL_PROVIDER=Ollama
```

## 步骤 3：设置 LLM 提供商

### 选项 A：本地 Ollama（推荐）

```bash
# 安装 Ollama
# macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: 从 https://ollama.com 下载安装

# 拉取模型
ollama pull llama3

# 验证
ollama list
```

配置中使用 `"llm_provider": "Ollama"` 和 `"llm_model_name": "llama3"`。

### 选项 B：OpenAI

```bash
pip install langchain-openai
export OPENAI_API_KEY="sk-..."
```

配置中使用 `"llm_provider": "OpenAI"` 和 `"llm_model_name": "gpt-4.1"`。

### 选项 C：Anthropic Claude

```bash
pip install langchain-anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 选项 D：Google Gemini

```bash
pip install langchain-google-genai
export GOOGLE_API_KEY="..."
```

### 验证 LLM 可用性

```python
from vnpy_ai.llm.models import get_available_providers

print(get_available_providers())  # 应输出已安装的 Provider 列表
```

## 步骤 4：在 VeighNa 中注册 AiHedgeFundApp

在 VeighNa 启动脚本（如 `run.py`）中添加：

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ai import AiHedgeFundApp


def main():
    qapp = create_qapp()
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    # 注册 AI Hedge Fund App
    main_engine.add_app(AiHedgeFundApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()
    qapp.exec()


if __name__ == "__main__":
    main()
```

或者通过 VeighNa 的 `vnpy_ai` 插件自动发现机制（如果已配置 `setup.py` 入口点）。

## 步骤 5：验证测试运行

### 1. 启动 VeighNa

```bash
python run.py
```

### 2. 在 GUI 中验证

- 确认 "AI Hedge Fund" 出现在应用列表中
- 打开 AI Hedge Fund 面板，确认状态显示正常
- 检查配置是否正确加载

### 3. 编程式验证

```python
from vnpy_ai.engine import AiHedgeFundEngine
from vnpy_ai.data_adapter import DataAdapter

# 检查引擎状态
engine = main_engine.get_engine("AiHedgeFund")
status = engine.get_status()
print(f"AI 启用: {status.enabled}")
print(f"自动交易: {status.auto_trading}")

# 测试数据适配器
adapter = DataAdapter(main_engine)
prices = adapter.get_prices("AAPL.SMART", "2024-01-01", "2024-12-31")
print(f"获取到 {len(prices)} 条价格数据")

# 测试工作流（不会实际下单，因为 auto_trading 未开启）
result = engine.run_workflow(["AAPL.SMART"])
for ticker, decision in result.decisions.items():
    print(f"{ticker}: {decision.action} (置信度: {decision.confidence})")
```

### 4. 运行测试套件

```bash
pytest tests/ -v
```

## 常见问题与排查

### Q: 启动时提示 "ModuleNotFoundError: No module named 'vnpy'"

**原因**: VeighNa 未安装或 Python 路径配置不正确。

**解决**:
```bash
pip install vnpy
# 或从源码安装
git clone https://github.com/vnpy/vnpy.git
cd vnpy && pip install -e .
```

### Q: AI 工作流返回所有 "hold" 决策

**原因**: 这是正常行为。LLM 不可用或 LangGraph 未安装时，工作流自动降级为 hold 策略。

**排查**:
1. 确认 LLM 依赖已安装：`pip list | grep langchain`
2. 确认 `.env` 或环境变量中 API Key 已正确配置
3. 检查日志中是否有 "LangGraph workflow failed, falling back to hold" 警告
4. 如果使用 Ollama，确认服务已启动：`ollama ps`

### Q: RPC 连接失败

**原因**: pyzmq 未安装或端口冲突。

**解决**:
```bash
pip install pyzmq
# 检查端口占用
netstat -an | grep 9001
```

### Q: 订单发送失败

**原因**: 网关未连接或配置不正确。

**排查**:
1. 确认 `gateway_name` 配置与 VeighNa 中连接的网关名称一致
2. 确认 `enable_auto_trading` 已设为 `true`
3. 检查 VeighNa 主界面中网关连接状态
4. 查看日志中的错误信息

### Q: 如何添加自定义分析师？

```python
from vnpy_ai.agents.base import AgentBase

class MyCustomAnalyst(AgentBase):
    agent_id = "my_custom"
    agent_name = "我的自定义分析师"

    def analyze(self, state):
        tickers = state["data"]["tickers"]
        prices = self.get_prices(tickers[0], state["data"]["start_date"], state["data"]["end_date"])
        # 自定义分析逻辑
        return {
            "agent_id": self.agent_id,
            "signal": "bullish",
            "confidence": 0.75,
            "reasoning": "基于自定义指标分析",
        }
```

然后在 `selected_analysts` 配置中添加 `"my_custom"`。

### Q: 如何选择不同触发频率？

| 频率 | 适用场景 | 注意事项 |
|------|---------|----------|
| `daily` | 日线策略、长期投资 | 每个交易日触发一次，推荐生产环境使用 |
| `bar` | 分钟级策略 | 注意 `signal_cooldown` 设置避免频繁触发 |
| `tick` | 高频策略 | 需要强大的 LLM 推理性能，不推荐生产环境 |

### Q: 数据不足怎么办？

- 确保 VeighNa 数据库中有足够的历史数据（`vnpy.trader.database`）
- 使用 VeighNa 的数据服务模块导入历史数据（如 RQData、TuShare 等）
- 通过 `get_prices` 返回的列表长度验证数据可用性