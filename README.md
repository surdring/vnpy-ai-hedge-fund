# VeighNa + AI Hedge Fund 整合项目

将 [VeighNa](https://github.com/vnpy/vnpy)（量化交易框架）与 [AI Hedge Fund](https://github.com/virattt/ai-hedge-fund)（多智能体投资决策系统）深度整合，构建端到端的 AI 驱动量化交易系统。

## 项目概述

本项目通过独立的 `vnpy_ai` 插件包，将 19 个 AI 投资分析师 Agent 的工作流嵌入 VeighNa 交易框架。系统保持**双进程架构**：VeighNa 主进程负责行情接收、订单执行、仓位管理；AI Agent 进程独立运行 LangGraph 工作流，通过 RPC 与主进程通信，避免依赖冲突。

### 核心特性

- **19 个 AI 分析师 Agent**：模拟巴菲特、彼得·林奇、迈克尔·伯里等知名投资人的投资风格，通过 LLM 生成交易信号
- **LangGraph 工作流引擎**：`Start → 19 Analysts（并行）→ Risk Manager → Portfolio Manager → OrderDispatcher → StatusSync → End`
- **14 种 LLM 提供商**：OpenAI、Ollama、Anthropic、Google、DeepSeek、Groq 等，支持本地模型优先
- **统一回测引擎**：支持 AI 模式、vnpy 模式、合并模式三种回测方式
- **双 UI 界面**：PySide6 桌面交易终端 + React Flow Web 工作流编辑器
- **降级容错**：LLM 不可用时自动切换为传统策略模式，不影响交易执行
- **配置驱动**：Agent 选择、LLM 提供商、数据源均通过配置控制，无需修改代码
- **Docker 一键部署**：完整的 Docker Compose 编排，支持生产级部署

## 架构概览

```
┌─────────────────────────────────────────────────────┐
│  VeighNa 主进程（PySide6 桌面 GUI）                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ 行情接收  │ │ 手动下单  │ │ 持仓/订单/成交监控 │   │
│  └──────────┘ └──────────┘ └──────────────────┘   │
│  ┌──────────────────────────────────────────────┐   │
│  │  AI Agent 菜单 → 启动 / 配置 / 信号监控       │   │
│  └──────────────────────────────────────────────┘   │
│         │ RPC (pyzmq)                               │
│         ▼                                           │
│  ┌──────────────────────────────────────────────┐   │
│  │  AI Agent 子进程（独立 Python 环境）           │   │
│  │  ┌────────────────────────────────────────┐  │   │
│  │  │  LangGraph 工作流                       │  │   │
│  │  │  [19 Analysts] → [Risk] → [Portfolio] │  │   │
│  │  └────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────┘   │
│         │ REST API                                  │
│         ▼                                           │
│  ┌──────────────────────────────────────────────┐   │
│  │  React Flow Web 编辑器（策略编排）            │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

## 目录结构

```
vnpy-ai-hedge-fund/
├── vnpy/                       # [源] VeighNa 核心框架（最小侵入修改）
│   └── vnpy/
│       ├── event/engine.py     # 事件驱动引擎
│       └── trader/             # 交易核心（engine, object, event, ui 等）
├── ai-hedge-fund/              # [源] AI Hedge Fund 源码（只读参考）
│   └── src/agents/             # 原始 Agent 实现
├── vnpy_ai/                    # [新建] AI Agent 策略插件包
│   ├── agents/                 # 21 个 Agent（19 分析师 + Risk + Portfolio）
│   │   └── upstream/           # 原始代码存档（含 LICENSE）
│   ├── workflow/               # LangGraph 工作流（state, graph, nodes, runner）
│   ├── llm/                    # LLM 抽象层（14 个提供商）
│   ├── backtesting/            # 统一回测引擎（ai/vnpy/merged 三种模式）
│   ├── data/                   # 数据适配与缓存
│   ├── tools/                  # API 工具集
│   ├── utils/                  # 工具函数（分析、可视化、进度）
│   ├── ui/                     # PySide6 UI 组件（设置、信号监控、分析器选择）
│   ├── engine.py               # AiHedgeFundEngine 主引擎
│   ├── app.py                  # VeighNa App 注册入口
│   ├── config.py               # 配置模型（Pydantic）
│   ├── rpc_bridge.py           # RPC 跨进程通信桥
│   ├── data_adapter.py         # 数据源适配层
│   ├── order_adapter.py        # 订单适配层
│   ├── event_adapter.py        # 事件适配层
│   ├── models.py               # 数据模型
│   └── monitoring.py           # 进程监控与结构化日志
├── vnpy_ai_web/                # [新建] Web 工作流编辑器
│   ├── backend/                # FastAPI 后端（REST API + 数据库）
│   │   ├── routes/             # API 路由（flows, hedge_fund, llm 等）
│   │   ├── services/           # 业务服务层
│   │   ├── database/           # SQLAlchemy 数据模型
│   │   └── repositories/       # 数据访问层
│   └── frontend/               # React + TypeScript 前端
│       └── src/
│           ├── components/     # UI 组件（Flow 编辑器、面板、设置）
│           ├── nodes/          # Agent 节点组件
│           ├── hooks/          # 交互逻辑 Hooks
│           └── services/       # API 调用服务
├── tests/                      # 整合测试（57 个）
│   ├── unit/                   # 单元测试
│   ├── integration/            # 集成测试
│   └── fixtures/               # 测试 Fixture
├── config/                     # 全局配置
│   ├── default_settings.json   # 默认设置
│   ├── llm_providers.json      # LLM 提供商配置
│   ├── agent_profiles/         # Agent 预设配置文件
│   └── .env.example            # 环境变量模板
├── docs/                       # 文档
│   ├── architecture.md         # 架构说明
│   ├── deployment_guide.md     # 部署指南
│   ├── migration_guide.md      # 迁移指南
│   ├── api_reference.md        # API 参考
│   └── agent_development_guide.md  # Agent 开发指南
├── examples/                   # 使用示例
│   ├── ai_agent_strategy/      # AI Agent 策略启动示例
│   ├── multi_agent_backtest/   # 多 Agent 回测示例
│   └── notebook/               # Jupyter Notebook 研究环境
├── docker/                     # Docker 部署配置
│   ├── Dockerfile.core         # VeighNa 核心镜像
│   ├── Dockerfile.agent        # AI Agent 镜像
│   ├── Dockerfile.web          # Web 前端镜像
│   └── docker-compose.yml      # 服务编排
└── zheng-docs/                 # 方案设计文档
    ├── VeighNa-AI-Hedge-Fund-整合方案.md
    ├── report-vnpy.md
    ├── report-AI Hedge Fund.md
    └── 实现审查报告.md
```

## 19 个 AI 分析师

| 分析师 | 投资风格 | 分析维度 |
|--------|---------|---------|
| Warren Buffett | 价值投资 | 护城河、管理层、长期竞争优势 |
| Benjamin Graham | 深度价值 | 安全边际、账面价值、市盈率 |
| Charlie Munger | 多元思维 | 商业模式质量、心理偏见 |
| Peter Lynch | 成长投资 | PEG 比率、业务可理解性 |
| Phil Fisher | 成长投资 | 研发投入、销售组织、利润率 |
| Bill Ackman | 激进投资 | 催化剂事件、公司治理 |
| Cathie Wood | 颠覆创新 | 技术颠覆潜力、创新溢价 |
| Stanley Druckenmiller | 宏观交易 | 宏观趋势、流动性、央行政策 |
| Michael Burry | 逆向投资 | 市场泡沫、信用风险、非对称押注 |
| Nassim Taleb | 尾部风险 | 黑天鹅事件、凸性收益 |
| Aswath Damodaran | 估值模型 | DCF 模型、资本成本、终端价值 |
| Mohnish Pabrai | 模仿投资 | 克隆优质投资组合、低风险高不确定性 |
| Rakesh Jhunjhunwala | 新兴市场 | 印度市场、宏观增长、行业轮动 |
| Fundamentals | 基本面 | 财务比率、收入增长、盈利能力 |
| Technicals | 技术面 | 趋势指标、动量、成交量 |
| Sentiment | 情绪面 | 市场情绪、新闻情感分析 |
| Valuation | 估值 | 相对估值、DCF 建模 |
| Growth Agent | 成长 | 增长潜力、市场扩张、TAM |
| News Sentiment | 新闻情感 | 实时新闻情绪、事件驱动 |

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+（Web 前端）
- Ollama（可选，本地模型推理）

### 安装

```bash
# 克隆仓库
git clone <repo-url>
cd vnpy-ai-hedge-fund

# 安装核心依赖
pip install -e ".[agent,web]"

# 安装开发依赖
pip install -e ".[dev]"
```

### 配置

1. 复制环境变量模板并填写 API Key：

```bash
cp config/.env.example .env
```

2. 编辑 `config/default_settings.json` 配置 AI Agent 参数：

```json
{
  "enabled": false,
  "enable_auto_trading": false,
  "trigger_frequency": "daily",
  "selected_analysts": ["warren_buffett", "technicals", "fundamentals"],
  "llm_model_name": "llama3",
  "llm_provider": "Ollama",
  "max_position_ratio": 0.2,
  "fallback_strategy": "hold"
}
```

> **重要**：`enable_auto_trading` 默认为 `false`，AI 决策仅作为信号输出，不会自动下单。确认策略无误后手动开启。

### 启动 VeighNa 桌面交易终端

```python
# examples/ai_agent_strategy/run.py
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy_ai.app import AiHedgeFundApp

event_engine = EventEngine()
main_engine = MainEngine(event_engine)
engine = main_engine.add_app(AiHedgeFundApp)

# 启动 AI Agent 子进程
engine.start_agent_process()
```

### 启动 Web 工作流编辑器

```bash
# 启动后端 API
cd vnpy_ai_web/backend
python main.py

# 启动前端开发服务器
cd vnpy_ai_web/frontend
npm install
npm run dev
```

### Docker 一键部署

```bash
cd docker
docker-compose up -d
```

## 运行测试

```bash
# 全部测试
pytest tests/ -v

# 仅单元测试
pytest tests/unit/ -v

# 仅集成测试
pytest tests/integration/ -v

# 仅 vnpy_ai 相关测试
pytest tests/ -v -k vnpy_ai
```

## 设计原则

1. **最小侵入**：不修改 `vnpy/` 和 `ai-hedge-fund/` 核心框架源码，仅通过插件机制扩展
2. **代码复制 + 适配**：从 `ai-hedge-fund/` 移植 Agent 代码，保留原始作者信息，不修改源文件
3. **进程隔离**：AI Agent 工作流在独立进程中运行，通过 RPC 与 vnpy 主进程通信
4. **降级容错**：LLM 不可用时自动降级为传统策略模式，不影响交易执行
5. **配置驱动**：Agent 选择、LLM 提供商、数据源均通过配置控制

## 技术栈

| 层级 | 技术 |
|------|------|
| 交易框架 | VeighNa (PySide6, EventEngine) |
| AI 工作流 | LangGraph, LangChain |
| LLM 提供商 | OpenAI, Ollama, Anthropic, Google, DeepSeek, Groq 等 14 种 |
| 数据模型 | Pydantic v2, dataclasses |
| 进程通信 | pyzmq (RPC) |
| Web 后端 | FastAPI, SQLAlchemy, Alembic |
| Web 前端 | React 18, TypeScript, Vite, React Flow, Tailwind CSS |
| 回测 | NumPy, Pandas, 统一回测引擎 |
| 部署 | Docker, Docker Compose |
| 测试 | pytest (57 个测试) |
| 代码质量 | ruff, mypy |

## 文档索引

- [整合方案设计](zheng-docs/VeighNa-AI-Hedge-Fund-整合方案.md) — 完整的架构设计、模块职责、实施路线图
- [实现审查报告](zheng-docs/实现审查报告.md) — 三轮审查结论，覆盖所有规划项的实现状态
- [VeighNa 深度分析](zheng-docs/report-vnpy.md) — 源项目能力评估
- [AI Hedge Fund 深度分析](zheng-docs/report-AI%20Hedge%20Fund.md) — 源项目能力评估
- [架构说明](docs/architecture.md) — 系统架构概览
- [部署指南](docs/deployment_guide.md) — 生产环境部署
- [API 参考](docs/api_reference.md) — REST API 接口文档
- [Agent 开发指南](docs/agent_development_guide.md) — 自定义 Agent 开发

## 许可证

本项目采用 MIT 许可证。详情参见 [LICENSE](LICENSE)。

`ai-hedge-fund/` 和 `vnpy_ai/agents/upstream/` 中的原始代码遵循其各自的开源许可证。