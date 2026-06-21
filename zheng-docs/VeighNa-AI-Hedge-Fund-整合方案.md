# VeighNa + AI Hedge Fund 整合方案

> **版本**: 1.0
> **日期**: 2026-06-17
> **状态**: 方案设计阶段

---

## 目录

0. [开发环境与源码准备](#0-开发环境与源码准备)
1. [整合愿景与目标](#1-整合愿景与目标)
2. [源项目能力盘点](#2-源项目能力盘点)
3. [整合架构设计](#3-整合架构设计)
4. [目录结构规划](#4-目录结构规划)
5. [模块职责详述](#5-模块职责详述)
6. [数据流与通信协议](#6-数据流与通信协议)
7. [分阶段实施路线图](#7-分阶段实施路线图)
8. [风险与缓解措施](#8-风险与缓解措施)
9. [运维与部署方案](#9-运维与部署方案)

---

## 0. 开发环境与源码准备

### 0.1 是否需要提前下载源码

**需要。** 整合开发依赖两个源代码仓库，必须在开发前将源码克隆/复制到本地工作目录。后续的模块移植、接口适配、集成测试均在此基础上进行。

### 0.2 源码存放位置

两个项目已就绪，存放位置如下：

| 项目 | 存放路径 | 来源 | 说明 |
|------|---------|------|------|
| **VeighNa** | `d:\develop\vnpy-ai-hedge-fund\vnpy\` | 从 `d:\develop\vnpy-4.4.0\` 复制¹ | 核心框架保持原样，仅做最小侵入式修改 |
| **AI Hedge Fund** | `d:\develop\vnpy-ai-hedge-fund\ai-hedge-fund\` | 从 `https://github.com/virattt/ai-hedge-fund` 克隆 | 作为 Agent 策略源码来源，以**只读方式引用** |

> ¹ 首次复制后，VeighNa 的原始位置 `d:\develop\vnpy-4.4.0\` 不再需要维护，后续所有开发均以 `d:\develop\vnpy-ai-hedge-fund\vnpy\` 为准。

### 0.3 整合项目与源项目的关系

整合遵循**源项目与整合代码分离**的原则：

- **源项目聚合**：VeighNa 和 AI Hedge Fund 的源码统一放置在 `d:\develop\vnpy-ai-hedge-fund\` 根目录下，与整合代码同属一个仓库，便于版本管理和协同开发。
- **只读对待**：`vnpy\` 和 `ai-hedge-fund\` 目录的代码保持原样，不做破坏性修改。vnpy 仅做极少量新增（事件类型常量、数据类），AI Hedge Fund 完全不修改。
- **整合代码独立**：`vnpy_ai/` 和 `vnpy_ai_web/` 作为独立包新建，代码以**复制 + 适配**方式从 AI Hedge Fund 移植，保留原始作者信息。
- **后续升级策略**：当源项目发布新版本时，将新版代码替换对应目录（`vnpy\` 或 `ai-hedge-fund\`），重新评估影响范围。

### 0.4 工作目录结构概览

```
d:\develop\
└── vnpy-ai-hedge-fund\               # 整合项目根目录（Git 仓库根目录）
    ├── vnpy\                         # [源] VeighNa 核心框架
    │   ├── alpha\
    │   ├── event\
    │   │   └── engine.py
    │   ├── trader\
    │   │   ├── engine.py             # 新增 add_ai_agent() 方法
    │   │   ├── object.py             # 新增 AiSignalData 数据类
    │   │   ├── event.py              # 新增 AI 事件类型常量
    │   │   ├── ui\
    │   │   │   ├── mainwindow.py     # 新增 AI Agent 面板菜单项
    │   │   │   └── widget.py
    │   │   └── locale\...
    │   └── ...                       # 其他 vnpy 子模块
    │
    ├── ai-hedge-fund\                # [源] AI Hedge Fund 源码（只读）
    │   ├── src\
    │   │   ├── agents\               # 19 + 2 Agent 源码
    │   │   ├── backtesting\          # 回测引擎
    │   │   ├── cli\
    │   │   ├── data\                 # 数据模型与缓存
    │   │   ├── graph\                # LangGraph 工作流
    │   │   ├── llm\                  # LLM 抽象层
    │   │   ├── tools\
    │   │   ├── utils\
    │   │   └── main.py               # 工作流入口
    │   ├── app\                      # Web 工作流编辑器
    │   │   ├── backend\
    │   │   └── frontend\
    │   ├── v2\                       # V2 实验架构
    │   └── pyproject.toml
    │
    ├── vnpy_ai\                      # [新建] AI Agent 策略插件包
    │   ├── __init__.py
    │   ├── app.py                    # AiHedgeFundApp
    │   ├── engine.py                 # AiHedgeFundEngine
    │   ├── rpc_bridge.py
    │   ├── event_adapter.py
    │   ├── data_adapter.py
    │   ├── order_adapter.py
    │   ├── agents\                   # 从 ai-hedge-fund/src/agents/ 移植
    │   ├── workflow\
    │   ├── llm\
    │   ├── backtesting\
    │   ├── data\
    │   └── ui\
    │
    ├── vnpy_ai_web\                  # [新建] Web 工作流编辑器
    │   ├── backend\                  # 从 ai-hedge-fund/app/backend/ 移植
    │   └── frontend\                 # 从 ai-hedge-fund/app/frontend/ 移植
    │
    ├── tests\
    ├── examples\
    ├── docs\
    ├── config\
    ├── docker\
    ├── pyproject.toml
    ├── README.md
    └── .gitignore
```

### 0.5 开发环境要求

| 项目 | 环境要求 |
|------|---------|
| Python | 3.11+（推荐 3.13） |
| 包管理 | Poetry（主） + pnpm（Web 前端） |
| VeighNa 环境 | 从 `d:\develop\vnpy-4.4.0\` 复制 `vnpy\` 目录到整合项目根目录后即可使用 |
| AI Hedge Fund 环境 | 克隆到整合项目根目录下的 `ai-hedge-fund\` 目录，作为参考源码无需安装其依赖。移植 Agent 时提取所需依赖加入 `vnpy_ai` 包 |
| 版本控制 | Git，仓库根目录为 `d:\develop\vnpy-ai-hedge-fund\`，源项目与整合代码统一管理 |

### 0.6 首次开发启动步骤

```
1. 创建整合项目目录：d:\develop\vnpy-ai-hedge-fund\
2. 从 d:\develop\vnpy-4.4.0\ 复制 vnpy\ 目录到整合项目根目录
3. 克隆 AI Hedge Fund 源码：git clone https://github.com/virattt/ai-hedge-fund.git d:\develop\vnpy-ai-hedge-fund\ai-hedge-fund\
4. 使用 Poetry 初始化整合项目，声明 vnpy_ai 和 vnpy_ai_web 为子包
5. 开始 Phase 1 开发（数据适配层）
```

---

## 1. 整合愿景与目标

### 1.1 整合定位

构建一个 **AI 驱动的全栈量化交易平台**，将 VeighNa 的生产级交易执行能力与 AI Hedge Fund 的 LLM 多智能体决策能力深度融合，形成"传统策略引擎 + AI 智能决策"双引擎架构。

### 1.2 核心目标

| 目标 | 描述 | 成功标准 |
|------|------|---------|
| 智能决策接入 | AI Hedge Fund 的 21 个 Agent 可作为 vnpy 的策略插件运行 | 可通过 vnpy 界面加载 AI Agent 策略 |
| 数据源统一 | AI Agent 直接使用 vnpy 的数据服务和数据库，不再依赖单一 Financial Datasets API | 数据获取链路数从 1 条扩展至 10+ 条 |
| 实盘交易联动 | Agent 决策信号通过 vnpy 的 OMS 和 Gateway 直接下单 | 完成从信号生成到报单的端到端链路 |
| 回测统一 | 复用了 vnpy 的回测框架，同时保留 AI Hedge Fund 的绩效指标体系 | 统一的回测入口和结果输出 |
| 体验整合 | React Flow 工作流编辑器作为 vnpy 的可选 Web 界面 | 用户可拖拽编排 Agent 协作拓扑 |

### 1.3 设计原则

1. **最小侵入**：不修改 vnpy 核心框架（MainEngine/EventEngine/OmsEngine），仅通过插件机制扩展
2. **进程隔离**：AI Agent 工作流在独立进程中运行，通过 RPC 与 vnpy 主进程通信，避免 LangChain 依赖污染 vnpy 核心环境
3. **降级容错**：LLM 不可用时，Agent 工作流自动降级为传统策略模式，不影响交易执行
4. **渐进式集成**：分三个 Phase 逐步交付，每个 Phase 有独立可用的产出物
5. **配置驱动**：Agent 选择、LLM 提供商、数据源均通过配置控制，无需修改代码

---

## 2. 源项目能力盘点

### 2.1 VeighNa (vnpy) 能力矩阵

| 能力域 | 核心模块 | 对外接口 | 整合中的角色 |
|--------|---------|---------|-------------|
| 事件驱动 | EventEngine | `register()`, `put()` | 系统事件总线，Agent 信号事件源 |
| 主引擎 | MainEngine | `send_order()`, `subscribe()`, `add_app()`, `connect()` | 交易执行中枢，Agent 策略注册入口 |
| 订单管理 | OmsEngine | `get_order()`, `get_trade()`, `get_position()`, `get_tick()` | 运行时状态查询，Agent 决策上下文 |
| 交易接口 | BaseGateway | `connect()`, `send_order()`, `cancel_order()`, `subscribe()` | 实盘/仿真交易通道，20+ 个实现 |
| 数据库 | BaseDatabase | `save_bar_data()`, `load_bar_data()`, `get_bar_overview()` | 历史数据存储，Agent 回测数据源 |
| 数据服务 | BaseDatafeed | `query_bar_history()`, `query_tick_history()` | 外部数据源接入，9 个实现 |
| 应用插件 | BaseApp | `app_name`, `engine_class`, `widget_name` | Agent 策略的注册和加载机制 |
| 策略模板 | CtaTemplate | `on_tick()`, `on_bars()`, `on_order()`, `on_trade()` | Agent 策略的基类继承 |
| RPC 通讯 | RpcServer/RpcClient | `send_order()`, `subscribe()`, `query_history()` | 跨进程 Agent 通信桥梁 |
| 日志 | LogEngine | `write_log()` | 统一日志记录 |
| 通知 | EmailEngine/WechatEngine | `send_notification()` | Agent 决策结果推送 |

### 2.2 AI Hedge Fund 能力矩阵

| 能力域 | 核心模块 | 对外接口 | 整合中的角色 |
|--------|---------|---------|-------------|
| 多 Agent 编排 | LangGraph StateGraph | `add_node()`, `add_edge()`, `compile()` | 分析师 Agent 工作流拓扑 |
| 分析师 Agent | 19 个 Agent 函数 | `(state, agent_id) -> dict` | 投资决策信号生成 |
| 风险管理 | risk_management_agent | `(state, agent_id) -> dict` | 波动率仓位限制 |
| 投资组合管理 | portfolio_management_agent | `(state, agent_id) -> dict` | 信号综合决策 |
| LLM 抽象层 | get_model() / call_llm() | `(prompt, model_class) -> BaseModel` | 多提供商 LLM 调用 |
| 数据缓存 | Cache | `get_prices()`, `set_prices()`, `get_financial_metrics()` | 运行时数据缓存 |
| 回测引擎 | BacktestEngine | `run_backtest()` | 日频回测能力 |
| 绩效指标 | PerformanceMetrics | 夏普/Sortino/最大回撤 | 回测评估 |
| Web 工作流 | React Flow 编辑器 | REST API | 拖拽式 Agent 编排 |
| 数据持久化 | SQLAlchemy + Alembic | ORM 模型 | Web 端配置持久化 |

### 2.3 能力互补分析

```
VeighNa 提供（底层执行能力）          AI Hedge Fund 提供（上层决策能力）
┌─────────────────────────────┐        ┌─────────────────────────────┐
│ 实时行情接收 (Tick/Bar)      │        │ 19 智能体协作决策             │
│ 订单执行 (OMS + Gateway)    │        │ 多 LLM 提供商支持            │
│ 多市场接入 (20+ 接口)        │        │ 投资大师风格 Prompt 库       │
│ 数据持久化 (7 种数据库)      │        │ 波动率/相关性风控模型         │
│ 事件驱动架构                 │        │ Web 可视化工作流编辑器        │
│ 桌面 GUI (PySide6)          │        │ 回测 + 绩效指标报告           │
│ 策略回测框架                 │        │ Docker 部署支持              │
│ 国际化 / 通知推送            │        │ V2 事件研究 / 因子模型        │
└─────────────────────────────┘        └─────────────────────────────┘
            │                                       │
            └───────────────┬───────────────────────┘
                            ▼
              ┌─────────────────────────────┐
              │    整合后的 AI 量化平台       │
              │  传统策略 + AI 策略双引擎      │
              │  覆盖 20+ 市场 / 10+ 数据源    │
              │  桌面端 + Web 端双界面        │
              │  从研究到实盘全链路闭环        │
              └─────────────────────────────┘
```

---

## 3. 整合架构设计

### 3.1 总体架构

整合后的系统采用 **三层双进程架构**：

```
┌─────────────────────────────────────────────────────────────────────┐
│                        用户界面层                                    │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐  │
│  │ PySide6 桌面 GUI  │  │ React Flow Web   │  │ CLI 命令行入口    │  │
│  │ (vnpy 原生)       │  │ (AI HF 原生)     │  │ (统一入口)       │  │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘  │
│           │                     │                     │             │
├───────────┼─────────────────────┼─────────────────────┼─────────────┤
│           │           决策调度层 │                     │             │
│           │           ┌─────────▼─────────────────────▼──────┐      │
│           │           │         RPC 通信层 (pyzmq)           │      │
│           └───────────┤  ┌────────────────────────────────┐  │      │
│                       │  │  AiHedgeFundApp (进程 2)       │  │      │
│   ┌───────────────────┤  │  ┌──────────────────────────┐ │  │      │
│   │  vnpy 主进程       │  │  │ AiHedgeFundEngine        │ │  │      │
│   │  ┌──────────────┐ │  │  │ ┌──────────────────────┐ │ │  │      │
│   │  │ MainEngine   │ │  │  │ │ LangGraph Workflow   │ │ │  │      │
│   │  │ ┌──────────┐ │ │  │  │ │ ┌──────────────────┐ │ │ │  │      │
│   │  │ │EventEng  │ │ │  │   │  │ │ 19 Analyst Agent │ │ │ │  │      │
│   │  │ │OmsEngine │ │ │  │  │ │ ├──────────────────┤ │ │ │  │      │
│   │  │ │LogEngine │ │ │  │  │ │ │ Risk Manager     │ │ │ │  │      │
│   │  │ │NotifEng  │ │ │  │  │ │ ├──────────────────┤ │ │ │  │      │
│   │  │ └──────────┘ │ │  │  │ │ │ Portfolio Mgr    │ │ │ │  │      │
│   │  │ ┌──────────┐ │ │  │  │ │ └──────────────────┘ │ │ │  │      │
│   │  │ │ 20+       │ │ │  │  │ └──────────────────────┘ │ │  │      │
│   │  │ │ Gateways  │ │ │  │  │ ┌──────────────────────┐ │ │  │      │
│   │  │ └──────────┘ │ │  │  │ │ LLM 抽象层            │ │ │  │      │
│   │  │ ┌──────────┐ │ │  │  │ │ (14 提供商)            │ │ │  │      │
│   │  │ │ 8+ Apps   │ │ │  │  │ └──────────────────────┘ │ │  │      │
│   │  │ └──────────┘ │ │  │  │ └──────────────────────────┘ │  │      │
│   │  └──────────────┘ │  │  └────────────────────────────────┘  │      │
│   └───────────────────┘  └──────────────────────────────────────┘      │
│                                                                        │
├───────────────────────────────────────────────────────────────────────┤
│                            数据层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │ 7 种数据库    │  │ 9 种数据服务  │  │ Financial Datasets API       │ │
│  │ SQLite/MySQL │  │ RQData/Wind │  │ (AI HF 原有数据源)            │ │
│  │ PG/QuestDB  │  │ TuShare/...  │  │                              │ │
│  │ TDengine/... │  │              │  │                              │ │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────────┘
```

### 3.2 双进程设计说明

**为什么需要进程隔离？**

| 考量 | 说明 |
|------|------|
| 依赖冲突 | vnpy 核心依赖 PySide6/Qt6，AI Hedge Fund 依赖 LangChain/LangGraph，两者 Python 版本需求和底层 C 库存在潜在冲突 |
| 环境隔离 | AI Agent 的 LLM 调用可能长达数秒，如果阻塞 vnpy 主进程会导致 GUI 卡顿和实时行情丢失 |
| 独立扩展 | 两个进程可独立升级、独立部署，互不影响 |
| 故障隔离 | AI Agent 崩溃不影响 vnpy 主进程的交易执行，反之亦然 |

**通信机制**：vnpy 已内建 `vnpy.rpc` 模块（基于 pyzmq），直接复用。通信协议格式使用 JSON 序列化。

### 3.3 Agent 工作流拓扑

整合后的工作流在 LangGraph 原有拓扑基础上，增加了与 vnpy 的交互节点：

```
                        ┌─────────────┐
                        │  Start Node │
                        └──────┬──────┘
                               │
               ┌───────────────┼───────────────┐
               │               │               │
        ┌──────▼──────┐ ┌─────▼──────┐ ┌──────▼──────┐
        │ Buffett     │ │ Graham     │ │ ... 16 more │
        └──────┬──────┘ └─────┬──────┘ └──────┬──────┘
               │               │               │
               └───────────────┼───────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Risk Manager       │
                    │  ┌────────────────┐ │
                    │  │ 波动率计算      │ │
                    │  │ 相关性分析      │ │
                    │  │ VaR 计算       │ │
                    │  │ 仓位限制        │ │
                    │  └────────────────┘ │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Portfolio Manager   │
                    │  ┌────────────────┐ │
                    │  │ 信号综合评分    │ │
                    │  │ 操作约束计算    │ │
                    │  │ 最终决策        │ │
                    │  └────────────────┘ │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Order Dispatcher    │  ← 新增节点
                    │  ┌────────────────┐ │
                    │  │ 决策→OrderReq  │ │
                    │  │ RPC→MainEngine │ │
                    │  └────────────────┘ │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Status Sync Node    │  ← 新增节点
                    │  ┌────────────────┐ │
                    │  │ 同步持仓/订单    │ │
                    │  │ 同步账户状态    │ │
                    │  └────────────────┘ │
                    └──────────┬──────────┘
                               │
                            ┌──▼──┐
                            │ END │
                            └─────┘
```

### 3.4 事件流设计

整合后定义了以下新的 vnpy 事件类型，用于 Agent 与 vnpy 核心的事件通信：

| 事件类型 | 生产者 | 消费者 | 数据载荷 | 说明 |
|---------|--------|--------|---------|------|
| EVENT_AI_SIGNAL | AiHedgeFundEngine | 监控界面、日志 | dict `{ticker, agent, signal, confidence}` | 单个 Agent 产生的信号 |
| EVENT_AI_DECISION | AiHedgeFundEngine | OmsEngine、监控界面 | PortfolioManagerOutput | 最终投资组合决策 |
| EVENT_AI_DECISION_ORDER | AiHedgeFundEngine | MainEngine → Gateway | OrderRequest | 决策转化后的订单 |
| EVENT_AI_ERROR | AiHedgeFundEngine | LogEngine、通知引擎 | dict `{error_type, message, agent}` | AI Agent 异常 |
| EVENT_AI_STATUS | AiHedgeFundEngine | GUI 状态栏 | dict `{agent, status, progress}` | Agent 工作流进度 |

---

## 4. 目录结构规划

### 4.1 整合后项目根目录

```
vnpy-ai-hedge-fund/                        # 整合后项目根目录
├── vnpy/                                  # VeighNa 核心框架（保持原样）
│   ├── alpha/                             # AI 量化策略模块
│   ├── chart/                             # K 线图表组件
│   ├── event/                             # 事件驱动引擎
│   │   └── engine.py                      # 新增: EVENT_AI_SIGNAL 等事件类型常量
│   ├── rpc/                               # RPC 通讯组件（复用）
│   │   ├── server.py
│   │   ├── client.py
│   │   └── common.py
│   └── trader/                            # 核心交易平台
│       ├── engine.py                      # MainEngine 新增: add_ai_agent() 方法
│       ├── gateway.py
│       ├── object.py                      # 新增: AiSignalData 数据类
│       ├── setting.py
│       ├── database.py
│       ├── datafeed.py
│       ├── utility.py
│       ├── app.py
│       ├── converter.py
│       ├── ui/                            # Qt GUI 界面
│       │   ├── mainwindow.py              # 新增: AI Agent 面板菜单项
│       │   └── widget.py
│       └── locale/                        # 国际化翻译
│           └── zh_CN/LC_MESSAGES/
│               └── messages.po            # 新增: AI 相关翻译词条
│
├── vnpy_ai/                               # 新增: AI Agent 策略插件包
│   ├── __init__.py
│   ├── app.py                             # AiHedgeFundApp 类定义
│   ├── engine.py                          # AiHedgeFundEngine 主引擎
│   ├── rpc_bridge.py                      # 与 vnpy 主进程的 RPC 通信桥接
│   ├── event_adapter.py                   # Agent 事件与 vnpy Event 的适配转换
│   ├── data_adapter.py                    # vnpy 数据源适配层（替代 Financial Datasets API）
│   ├── order_adapter.py                   # Agent 决策到 OrderRequest 的转换
│   │
│   ├── agents/                            # 移植自 AI Hedge Fund src/agents/
│   │   ├── __init__.py
│   │   ├── base.py                        # 新增: Agent 基类（统一 vnpy 数据源）
│   │   ├── warren_buffett.py
│   │   ├── ben_graham.py
│   │   ├── bill_ackman.py
│   │   ├── cathie_wood.py
│   │   ├── charlie_munger.py
│   │   ├── michael_burry.py
│   │   ├── mohnish_pabrai.py
│   │   ├── nassim_taleb.py
│   │   ├── peter_lynch.py
│   │   ├── phil_fisher.py
│   │   ├── rakesh_jhunjhunwala.py
│   │   ├── stanley_druckenmiller.py
│   │   ├── aswath_damodaran.py
│   │   ├── growth_agent.py
│   │   ├── news_sentiment.py
│   │   ├── fundamentals.py
│   │   ├── sentiment.py
│   │   ├── technicals.py
│   │   ├── valuation.py
│   │   ├── risk_manager.py
│   │   └── portfolio_manager.py
│   │
│   ├── workflow/                          # LangGraph 工作流集成
│   │   ├── __init__.py
│   │   ├── state.py                       # AgentState 定义（扩展原有）
│   │   ├── graph.py                       # StateGraph 构建（含新增节点）
│   │   └── nodes.py                       # 新增: OrderDispatcher, StatusSync 节点
│   │
│   ├── llm/                               # LLM 抽象层（保持原样）
│   │   ├── __init__.py
│   │   ├── models.py                      # LLM 模型工厂
│   │   ├── api_models.json
│   │   └── ollama_models.json
│   │
│   ├── backtesting/                       # 整合回测能力
│   │   ├── __init__.py
│   │   ├── engine.py                      # 整合 BacktestEngine，增加 vnpy 回测适配
│   │   ├── controller.py
│   │   ├── trader.py
│   │   ├── metrics.py
│   │   ├── portfolio.py
│   │   ├── valuation.py
│   │   ├── output.py
│   │   ├── benchmarks.py
│   │   ├── types.py
│   │   └── vnpy_adapter.py                # 新增: vnpy BacktestingEngine 适配
│   │
│   ├── data/                              # 数据管理
│   │   ├── __init__.py
│   │   ├── models.py                      # Pydantic 数据模型
│   │   └── cache.py                       # 内存缓存
│   │
│   ├── tools/                             # 工具函数
│   │   ├── __init__.py
│   │   └── api.py
│   │
│   ├── utils/                             # 通用工具
│   │   ├── __init__.py
│   │   ├── analysts.py                    # 分析师注册表
│   │   ├── api_key.py                     # API Key 管理
│   │   ├── llm.py                         # LLM 调用封装
│   │   ├── display.py
│   │   ├── progress.py
│   │   └── visualize.py
│   │
│   └── ui/                                # 新增: Qt 配置界面
│       ├── __init__.py
│       ├── setting_widget.py              # Agent 参数配置面板
│       ├── analyst_selector.py            # 分析师选择组件
│       ├── model_config_widget.py         # LLM 模型配置面板
│       └── signal_monitor.py              # AI 信号实时监控面板
│
├── vnpy_ai_web/                           # 新增: Web 工作流编辑器（可选）
│   ├── backend/                           # 移植自 AI HF app/backend/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI 入口
│   │   ├── alembic/                       # 数据库迁移
│   │   │   ├── env.py
│   │   │   ├── script.py.mako
│   │   │   └── versions/
│   │   │       └── initial_migration.py
│   │   ├── database/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py
│   │   │   └── models.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── events.py
│   │   │   └── schemas.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── api_key_repository.py
│   │   │   ├── flow_repository.py
│   │   │   └── flow_run_repository.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── api_keys.py
│   │   │   ├── flow_runs.py
│   │   │   ├── flows.py
│   │   │   ├── health.py
│   │   │   ├── hedge_fund.py
│   │   │   ├── language_models.py
│   │   │   ├── ollama.py
│   │   │   └── storage.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── agent_service.py
│   │       ├── api_key_service.py
│   │       ├── backtest_service.py
│   │       ├── graph.py
│   │       ├── ollama_service.py
│   │       └── portfolio.py
│   │
│   └── frontend/                          # 移植自 AI HF app/frontend/（保持原样）
│       ├── package.json
│       ├── vite.config.ts
│       ├── index.html
│       └── src/
│           ├── App.tsx
│           ├── main.tsx
│           ├── components/
│           │   ├── Flow.tsx
│           │   ├── Layout.tsx
│           │   ├── custom-controls.tsx
│           │   ├── layout/
│           │   │   └── top-bar.tsx
│           │   ├── panels/
│           │   │   ├── left/
│           │   │   │   ├── left-sidebar.tsx
│           │   │   │   ├── flow-list.tsx
│           │   │   │   ├── flow-item.tsx
│           │   │   │   ├── flow-item-group.tsx
│           │   │   │   ├── flow-actions.tsx
│           │   │   │   ├── flow-context-menu.tsx
│           │   │   │   ├── flow-create-dialog.tsx
│           │   │   │   └── flow-edit-dialog.tsx
│           │   │   ├── right/
│           │   │   │   ├── right-sidebar.tsx
│           │   │   │   ├── component-list.tsx
│           │   │   │   ├── component-item.tsx
│           │   │   │   ├── component-item-group.tsx
│           │   │   │   └── component-actions.tsx
│           │   │   ├── bottom/
│           │   │   │   ├── bottom-panel.tsx
│           │   │   │   ├── tabs/
│           │   │   │   │   ├── index.ts
│           │   │   │   │   ├── output-tab.tsx
│           │   │   │   │   ├── output-tab-utils.ts
│           │   │   │   │   ├── backtest-output.tsx
│           │   │   │   │   ├── debug-console-tab.tsx
│           │   │   │   │   ├── problems-tab.tsx
│           │   │   │   │   ├── reasoning-content.tsx
│           │   │   │   │   ├── regular-output.tsx
│           │   │   │   │   └── terminal-tab.tsx
│           │   │   └── search-box.tsx
│           │   ├── settings/
│           │   │   ├── settings.tsx
│           │   │   ├── index.ts
│           │   │   ├── api-keys.tsx
│           │   │   ├── appearance.tsx
│           │   │   ├── models.tsx
│           │   │   └── models/
│           │   │       ├── cloud.tsx
│           │   │       └── ollama.tsx
│           │   ├── tabs/
│           │   │   ├── tab-bar.tsx
│           │   │   ├── tab-content.tsx
│           │   │   └── flow-tab-content.tsx
│           │   └── ui/                    # shadcn/ui 组件（保持原样）
│           ├── contexts/
│           │   ├── flow-context.tsx
│           │   ├── layout-context.tsx
│           │   ├── node-context.tsx
│           │   └── tabs-context.tsx
│           ├── data/
│           │   ├── agents.ts
│           │   ├── models.ts
│           │   ├── multi-node-mappings.ts
│           │   ├── node-mappings.ts
│           │   └── sidebar-components.ts
│           ├── edges/
│           │   └── index.ts
│           ├── hooks/
│           │   ├── use-component-groups.ts
│           │   ├── use-enhanced-flow-actions.ts
│           │   ├── use-flow-connection.ts
│           │   ├── use-flow-history.ts
│           │   ├── use-flow-management-tabs.ts
│           │   ├── use-flow-management.ts
│           │   ├── use-keyboard-shortcuts.ts
│           │   ├── use-mobile.tsx
│           │   ├── use-node-state.ts
│           │   ├── use-output-node-connection.ts
│           │   ├── use-resizable.ts
│           │   └── use-toast-manager.ts
│           ├── lib/
│           │   └── utils.ts
│           ├── nodes/
│           │   ├── index.ts
│           │   ├── types.ts
│           │   ├── utils.ts
│           │   └── components/
│           │       ├── agent-node.tsx
│           │       ├── agent-output-dialog.tsx
│           │       ├── investment-report-dialog.tsx
│           │       ├── investment-report-node.tsx
│           │       ├── json-output-dialog.tsx
│           │       ├── json-output-node.tsx
│           │       ├── node-shell.tsx
│           │       ├── output-node-status.tsx
│           │       ├── portfolio-manager-node.tsx
│           │       ├── portfolio-start-node.tsx
│           │       └── stock-analyzer-node.tsx
│           ├── providers/
│           │   └── theme-provider.tsx
│           ├── services/
│           │   ├── api.ts
│           │   ├── api-keys-api.ts
│           │   ├── backtest-api.ts
│           │   ├── flow-service.ts
│           │   ├── sidebar-storage.ts
│           │   ├── tab-service.ts
│           │   └── types.ts
│           ├── types/
│           │   └── flow.ts
│           └── utils/
│               ├── date-utils.ts
│               └── text-utils.ts
│
├── v2/                                    # AI HF V2 架构实验（保持原样，可选）
│   ├── backtesting/
│   ├── data/
│   ├── event_study/
│   ├── features/
│   ├── pipeline/
│   ├── portfolio/
│   ├── risk/
│   ├── signals/
│   ├── validation/
│   └── models.py
│
├── tests/                                 # 整合测试
│   ├── unit/                              # 单元测试
│   │   ├── test_data_adapter.py           # 数据适配器测试
│   │   ├── test_order_adapter.py          # 订单适配器测试
│   │   ├── test_event_adapter.py          # 事件适配器测试
│   │   ├── test_rpc_bridge.py             # RPC 通信测试
│   │   └── test_agent_base.py             # Agent 基类测试
│   ├── integration/                       # 集成测试
│   │   ├── test_agent_workflow.py         # Agent 工作流集成测试
│   │   ├── test_vnpy_integration.py       # vnpy 集成测试
│   │   ├── test_backtest_integration.py   # 回测集成测试
│   │   └── test_order_flow.py             # 端到端订单流测试
│   └── fixtures/                          # 测试数据
│       ├── mock_agent_outputs.py
│       ├── mock_market_data.py
│       └── mock_llm_responses.py
│
├── examples/                              # 使用示例
│   ├── ai_agent_strategy/                 # AI Agent 策略示例
│   │   ├── run.py                         # 启动脚本
│   │   └── config.json                    # 策略配置示例
│   ├── multi_agent_backtest/              # 多 Agent 回测示例
│   │   └── run.py
│   └── notebook/                          # Jupyter Notebook 投研示例
│       └── ai_agent_research.ipynb
│
├── docs/                                  # 文档
│   ├── architecture.md                    # 架构设计文档
│   ├── agent_development_guide.md         # Agent 开发指南
│   ├── deployment_guide.md                # 部署指南
│   ├── api_reference.md                   # API 参考
│   └── migration_guide.md                 # 迁移指南
│
├── config/                                # 全局配置
│   ├── default_settings.json              # 默认配置
│   ├── agent_profiles/                    # Agent 模板配置
│   │   ├── value_investing.json
│   │   ├── growth_investing.json
│   │   └── macro_trading.json
│   └── llm_providers.json                 # LLM 提供商配置
│
├── docker/                                # Docker 部署
│   ├── Dockerfile.core                    # vnpy 核心进程
│   ├── Dockerfile.agent                   # AI Agent 进程
│   ├── Dockerfile.web                     # Web 前端
│   ├── docker-compose.yml                 # 多服务编排
│   └── .env.example
│
├── pyproject.toml                         # Poetry 项目配置
├── README.md
├── CHANGELOG.md
├── LICENSE
└── .gitignore
```

### 4.2 目录职责总览

| 目录 | 定位 | 来源 | 说明 |
|------|------|------|------|
| `vnpy/` | 核心框架 | vnpy 原版 | 保持原样，仅做最小扩充（新增事件类型、AiSignalData 数据类） |
| `vnpy_ai/` | AI Agent 插件 | 新增 | 整合的核心，封装 Agent 工作流、数据适配、RPC 通信 |
| `vnpy_ai_web/` | Web 工作流编辑器 | AI HF 移植 | 可选模块，提供 React Flow 可视化界面 |
| `v2/` | 实验性架构 | AI HF 原版 | 保持原样，作为未来探索方向 |
| `tests/` | 整合测试 | 新增 | 覆盖数据适配、事件适配、RPC 通信、集成工作流 |
| `examples/` | 使用示例 | 新增 | 快速上手指南 |
| `docs/` | 文档 | 新增 | 架构设计、开发指南、部署指南 |
| `config/` | 全局配置 | 新增 | 统一配置文件管理 |

---

## 5. 模块职责详述

### 5.1 AiHedgeFundApp（vnpy_ai/app.py）

**职责**：实现 vnpy 的 BaseApp 接口，作为 AI Agent 策略的注册入口。

**核心类变量**：

| 变量 | 值 | 说明 |
|------|-----|------|
| app_name | "AiHedgeFund" | 应用的唯一标识名 |
| display_name | "AI 对冲基金" | 在 GUI 菜单中显示的名称 |
| engine_class | AiHedgeFundEngine | 关联的引擎类 |
| widget_name | "AiHedgeFundWidget" | 关联的 Qt 配置界面组件 |
| icon_name | "ai_hedge_fund.ico" | 应用图标文件 |

**与 vnpy 的交互方式**：
- 通过 MainEngine.add_app() 注册后，引擎自动初始化
- 使用时通过事件监听和 RPC 通信与 vnpy 核心交互

### 5.2 AiHedgeFundEngine（vnpy_ai/engine.py）

**职责**：AI Agent 工作流的主控制器，管理 Agent 生命周期、调度工作流执行、与 vnpy 核心通信。

**核心功能**：

| 功能 | 说明 |
|------|------|
| 工作流管理 | 初始化 LangGraph StateGraph，编译工作流，支持选择特定分析师 |
| 信号订阅 | 订阅 vnpy 的 EVENT_TICK/EVENT_BAR 事件，按配置的触发频率启动 Agent 工作流 |
| 数据获取 | 通过 data_adapter 从 vnpy 的数据服务和数据库获取所需的行情和财务数据 |
| 决策执行 | 将 Portfolio Manager 的输出通过 order_adapter 转换为 OrderRequest，发送到 MainEngine |
| 状态同步 | 定期从 OmsEngine 同步持仓、订单、账户状态，更新 Agent 工作流上下文 |
| 降级处理 | LLM 不可用时，使用预定义的降级策略（如保持持仓不变、仅使用传统技术指标） |
| 进度上报 | 推送 EVENT_AI_STATUS 事件，供 GUI 监控面板显示 Agent 工作状态 |

**配置项**：

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| trigger_frequency | str | "daily" | 工作流触发频率（tick/bar/15min/daily） |
| selected_analysts | list[str] | 全部 | 选择的分析师列表 |
| llm_model_name | str | "gpt-4.1" | LLM 模型名称 |
| llm_provider | str | "OpenAI" | LLM 提供商 |
| max_position_ratio | float | 0.2 | 单标的仓位上限比例 |
| enable_auto_trading | bool | False | 是否启用自动下单 |
| signal_cooldown | int | 300 | 信号冷却时间（秒） |
| fallback_strategy | str | "hold" | LLM 降级策略（hold/flat/sma_cross） |

### 5.3 RPC Bridge（vnpy_ai/rpc_bridge.py）

**职责**：实现 vnpy 主进程与 AI Agent 进程之间的双向通信。

**通信协议**：

| 消息类型 | 方向 | 内容 | 说明 |
|---------|------|------|------|
| REQUEST_MARKET_DATA | Agent → vnpy | `{ticker, start_date, end_date, fields}` | 请求行情数据 |
| RESPONSE_MARKET_DATA | vnpy → Agent | `{ticker, data: list[dict]}` | 返回行情数据 |
| REQUEST_PORTFOLIO | Agent → vnpy | `{}` | 请求当前持仓和账户状态 |
| RESPONSE_PORTFOLIO | vnpy → Agent | `{cash, positions, margin_used, ...}` | 返回账户状态 |
| SUBMIT_ORDER | Agent → vnpy | `{ticker, action, quantity, price}` | 提交订单 |
| ORDER_STATUS | vnpy → Agent | `{order_id, status, filled_qty}` | 订单状态回报 |
| AGENT_SIGNAL | Agent → vnpy | `{ticker, agent, signal, confidence}` | 推送 Agent 信号（用于监控） |
| HEARTBEAT | 双向 | `{timestamp}` | 心跳检测 |

**连接管理**：
- 使用 vnpy.rpc 模块的 RpcServer/RpcClient 实现
- Agent 进程作为 RPC 客户端，连接 vnpy 主进程的 RPC 服务端
- 支持断线重连，重连间隔 5 秒，最大重试 10 次
- 心跳间隔 30 秒，连续 3 次未收到心跳视为断开

### 5.4 Event Adapter（vnpy_ai/event_adapter.py）

**职责**：将 Agent 工作流产生的信号和决策转换为 vnpy EventEngine 的事件格式，并注册到事件总线。

**事件映射关系**：

| Agent 内部信号 | vnpy 事件类型 | 转换逻辑 |
|---------------|-------------|---------|
| Agent 生成 buy/sell 信号 | EVENT_AI_SIGNAL | 将 AnalystSignal 转换为 AiSignalData 对象 |
| Portfolio Manager 最终决策 | EVENT_AI_DECISION | 将 PortfolioManagerOutput 拆分为多个 EVENT_AI_DECISION_ORDER |
| Agent 执行异常 | EVENT_AI_ERROR | 封装异常信息，写入日志并推送通知 |
| 工作流状态变更 | EVENT_AI_STATUS | 更新 GUI 进度条和状态文本 |

### 5.5 Data Adapter（vnpy_ai/data_adapter.py）

**职责**：将 vnpy 的数据源（数据库和数据服务）适配为 AI Agent 期望的数据格式，替代原有的 Financial Datasets API 调用。

**数据映射关系**：

| Agent 需要的数据 | vnpy 数据源 | 获取方式 |
|-----------------|-----------|---------|
| 日线价格数据 (OHLCV) | BaseDatabase.load_bar_data() | 从本地数据库读取 |
| 实时 Tick 数据 | OmsEngine.get_tick() | 从内存缓存获取 |
| 财务指标 (PE/PB/ROE等) | BaseDatafeed 实现（如 RQData） | 通过 RPC 调用数据服务 |
| 公司新闻 | BaseDatafeed 实现（如 TuShare） | 通过 RPC 调用数据服务 |
| 内部交易 | BaseDatafeed 实现（如 Wind） | 通过 RPC 调用数据服务 |
| 市场数据（市值等） | BaseDatafeed 实现 | 通过 RPC 调用数据服务 |

**缓存策略**：
- 复用 vnpy 的 OmsEngine 内存缓存（Tick、订单、持仓）
- 数据库查询结果由 Agent 进程的 Cache 类管理
- 数据服务查询结果设置 TTL（默认 1 小时），避免重复调用

### 5.6 Order Adapter（vnpy_ai/order_adapter.py）

**职责**：将 Portfolio Manager 输出的交易决策转换为 vnpy 标准的 OrderRequest 对象。

**决策到订单的转换规则**：

| Portfolio Manager Action | vnpy OrderRequest | 说明 |
|-------------------------|-------------------|------|
| buy | Direction.LONG, Offset.OPEN | 买入开仓 |
| sell | Direction.LONG, Offset.CLOSE | 卖出平仓 |
| short | Direction.SHORT, Offset.OPEN | 做空开仓 |
| cover | Direction.SHORT, Offset.CLOSE | 做空平仓 |
| hold | 不生成订单 | 保持持仓 |

**附加校验**：
- 方向校验：核对 action 与当前持仓的一致性
- 数量校验：检查 quantity 是否超过持仓数量或资金限制
- 价格校验：如果是限价单，检查价格是否在合理范围内
- 交易所校验：通过 vnpy 的合约信息确认 ticker 对应的交易所

### 5.7 Agent 基类（vnpy_ai/agents/base.py）

**职责**：为所有 19 个 Agent 提供统一的基类，封装数据获取、LLM 调用、信号写入的通用流程。

**基类提供的通用能力**：

| 能力 | 说明 |
|------|------|
| 数据获取 | 统一通过 data_adapter 获取数据，而非直接调用 Financial Datasets API |
| 状态访问 | 通过 state 统一访问 tickers、日期、portfolio 等上下文 |
| 信号写入 | 统一的信号格式和写入路径 |
| 错误处理 | 统一的异常捕获和降级逻辑 |
| 进度上报 | 统一的进度状态更新 |

### 5.8 工作流节点（vnpy_ai/workflow/）

**state.py 扩展**：
- 在原 AgentState 基础上增加 `execution_context` 字段（包含 vnpy 连接状态、订单状态等）
- 增加 `order_results` 字段（记录已发送订单的结果）

**nodes.py 新增节点**：

| 节点 | 说明 |
|------|------|
| OrderDispatcher | 将 Portfolio Manager 决策转换为 OrderRequest，通过 RPC 发送到 vnpy 主进程 |
| StatusSync | 从 vnpy 主进程同步当前持仓、订单、账户状态，更新 AgentState |
| FallbackHandler | 当 LLM 调用失败时，执行降级策略 |

**graph.py 扩展**：
- 在 Portfolio Manager 之后插入 OrderDispatcher 节点
- 在 OrderDispatcher 之后插入 StatusSync 节点
- 在 Start 节点之前插入 Risk Manager 的数据预处理步骤
- 可选择是否插入 FallbackHandler 节点（默认开启）

### 5.9 vnpy 核心最小修改

**vnpy/trader/object.py 新增**：

| 新增内容 | 说明 |
|---------|------|
| AiSignalData 数据类 | 定义 AI Agent 信号的数据结构（agent_name, ticker, signal, confidence, reasoning, timestamp） |
| AiDecisionData 数据类 | 定义 AI 决策的数据结构（ticker, action, quantity, confidence, agent_signals, risk_metrics） |

**vnpy/trader/event.py 新增常量**：

| 常量 | 值 | 说明 |
|------|-----|------|
| EVENT_AI_SIGNAL | "eAiSignal" | AI Agent 信号事件 |
| EVENT_AI_DECISION | "eAiDecision" | AI 最终决策事件 |
| EVENT_AI_DECISION_ORDER | "eAiDecisionOrder" | AI 决策产生的订单事件 |
| EVENT_AI_ERROR | "eAiError" | AI Agent 异常事件 |
| EVENT_AI_STATUS | "eAiStatus" | AI Agent 状态更新事件 |

---

## 6. 数据流与通信协议

### 6.1 完整数据流（单次决策循环）

```
Phase 1: 触发
  vnpy Gateway 接收行情 → EventEngine.put(EVENT_BAR) → AiHedgeFundEngine.on_bars()
  → AiHedgeFundEngine 检查触发条件（频率、冷却时间）

Phase 2: 数据准备
  AiHedgeFundEngine → data_adapter.get_financial_data(tickers) → 
    ├─ RPC 请求 → vnpy 主进程 → BaseDatabase.load_bar_data()
    └─ RPC 请求 → vnpy 主进程 → BaseDatafeed.query_history()
  → 返回 DataFrame/Price 列表

Phase 3: Agent 工作流执行
  LangGraph 编译器执行 StateGraph：
    Start → Agent1 → Agent2 → ... → Agent19 
    → Risk Manager → Portfolio Manager → OrderDispatcher → StatusSync → End

  每个 Agent 内部：
    data_adapter.get_data() → 构建 Prompt → LLM 调用 → 解析结构化输出 → 写入 AgentState

Phase 4: 订单执行
  OrderDispatcher → order_adapter.decision_to_order() → RPC 请求 → vnpy 主进程
  → MainEngine.send_order() → Gateway.send_order() → 交易所

Phase 5: 状态同步
  StatusSync → RPC 请求 → vnpy 主进程
  → OmsEngine.get_portfolio() → 返回持仓/订单/账户状态
  → 更新 AgentState.execution_context

Phase 6: 事件推送
  Agent 信号 → EventAdapter → EVENT_AI_SIGNAL → GUI 监控面板更新
  最终决策 → EventAdapter → EVENT_AI_DECISION → 日志/通知
  订单发送 → EventAdapter → EVENT_AI_DECISION_ORDER → OmsEngine 跟踪
```

### 6.2 进程间通信架构

```
┌──────────────────────────────────────────────────────────────────┐
│                      vnpy 主进程                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  RpcServer (port 9001)                                     │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Handlers:                                            │  │  │
│  │  │  - get_market_data(command)  →  query database/datafeed │  │
│  │  │  - get_portfolio(command)    →  OmsEngine 查询        │  │  │
│  │  │  - submit_order(command)     →  MainEngine.send_order │  │  │
│  │  │  - cancel_order(command)     →  MainEngine.cancel_order│  │  │
│  │  │  - subscribe(command)        →  MainEngine.subscribe  │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  RpcClient (port 9002, 连接 Agent 进程的 Server)            │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ 接收: Agent 信号推送、状态更新、心跳                    │  │  │
│  │  │ 发送: 行情数据推送 (EVENT_TICK/EVENT_BAR 转发)         │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │  pyzmq (TCP)
                              │
┌─────────────────────────────▼────────────────────────────────────┐
│                      AI Agent 进程                                │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  RpcClient (连接 vnpy 主进程 port 9001)                     │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ 发送: 数据请求、订单提交、心跳                           │  │  │
│  │  │ 接收: 行情数据、账户状态、订单回报                       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  RpcServer (port 9002, 接收 vnpy 主进程连接)                │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │ Handlers:                                            │  │  │
│  │  │  - on_market_data(data)   →  触发 Agent 工作流        │  │  │
│  │  │  - on_order_status(status) → 更新 AgentState          │  │  │
│  │  │  - on_heartbeat()         →  心跳响应                 │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  AiHedgeFundEngine                                         │  │
│  │  ┌──────────────────────────────────────────────────────┐  │  │
│  │  │  - 管理 Agent 生命周期                                │  │  │
│  │  │  - 调度 LangGraph 工作流                              │  │  │
│  │  │  - 协调 RPC 通信                                      │  │  │
│  │  │  - 降级策略执行                                       │  │  │
│  │  └──────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 消息格式规范

所有 RPC 消息采用 JSON 格式，统一结构：

```
{
    "type": "消息类型标识",
    "timestamp": "ISO 8601 时间戳",
    "request_id": "唯一请求 ID（用于响应匹配）",
    "payload": { ... }  // 具体消息内容
}
```

---

## 7. 分阶段实施路线图

### 7.1 Phase 1：数据层整合（预计 2-3 周）

**目标**：AI Agent 可以使用 vnpy 的数据源获取数据，不再唯一依赖 Financial Datasets API。

**交付物**：

| 交付物 | 描述 |
|--------|------|
| data_adapter.py | 实现 vnpy 数据源到 Agent 数据格式的适配 |
| base.py (Agent 基类) | 统一 Agent 的数据获取逻辑 |
| 单元测试 | 数据适配器的正确性测试 |

**技术要点**：
- 不修改任何 Agent 源码，仅在基类中切换数据获取路径
- 保留 Financial Datasets API 作为备选数据源
- 数据格式统一为 Pydantic 模型（Price/FinancialMetrics 等）

**验证标准**：
- 使用 vnpy 本地数据库中的历史数据，运行单次 AI Hedge Fund 分析
- 输出结果与使用 Financial Datasets API 的结果一致

### 7.2 Phase 2：策略层整合（预计 4-6 周）

**目标**：AI Agent 工作流作为 vnpy App 插件运行，生成的决策信号可通过 vnpy 的事件系统传播，支持仿真交易。

**交付物**：

| 交付物 | 描述 |
|--------|------|
| AiHedgeFundApp | 实现 BaseApp 接口 |
| AiHedgeFundEngine | 实现 Agent 工作流管理，订阅 vnpy 事件 |
| rpc_bridge.py | 进程间通信实现 |
| event_adapter.py | Agent 事件到 vnpy 事件转换 |
| order_adapter.py | 决策到 OrderRequest 转换 |
| workflow/nodes.py | OrderDispatcher 和 StatusSync 节点 |
| Qt UI 面板 | Agent 参数配置和信号监控界面 |
| 仿真交易集成测试 | 端到端订单流测试 |

**技术要点**：
- Agent 进程与 vnpy 主进程独立部署
- 使用 vnpy.rpc 模块实现双向通信
- 在 OmsEngine 中注册 AI 决策事件的处理逻辑
- 支持手动确认模式（Agent 生成信号，用户确认后下单）

**验证标准**：
- 在 vnpy 桌面端加载 AI Agent 策略
- 连接仿真交易接口（如 CTP SimNow）
- Agent 工作流触发后，信号正确显示在 GUI 监控面板
- 手动确认后订单正确发送到仿真环境

### 7.3 Phase 3：UI 整合与生产化（预计 6-8 周）

**目标**：Web 工作流编辑器可用，回测引擎统一，生产环境部署就绪。

**交付物**：

| 交付物 | 描述 |
|--------|------|
| 统一回测引擎 | 整合 vnpy BacktestingEngine 和 AI HF BacktestEngine |
| Docker 部署方案 | 多服务 Docker Compose 编排 |
| 配置中心 | 统一配置文件管理 |
| 通知集成 | Agent 决策通过邮件/微信通知 |
| 生产级日志 | 结构化日志和审计追踪 |
| 性能测试报告 | 延迟、吞吐量、资源消耗 |
| 部署文档 | 完整的部署和运维指南 |

**技术要点**：
- 回测引擎支持参数化选择（vnpy 原生回测 / AI HF 回测 / 合并回测）
- Docker Compose 编排三个服务：vnpy 核心、AI Agent、Web 前端
- 日志使用 loguru 结构化输出，支持 JSON 格式

**验证标准**：
- 完整的 CI/CD 流水线通过
- Docker 一键部署成功
- 回测结果与独立运行的结果一致
- 生产环境稳定运行 7 天无异常

### 7.4 里程碑总览

```
Week 0 ──────────────────────────────────────────────────────────────
        │ 方案设计评审
        │
Week 2 ──● Phase 1 完成
        │ 数据适配器交付
        │
Week 4 ──┤
        │ Phase 2 开发中
        │
Week 6 ──● Phase 2 完成
        │ 策略插件交付，仿真交易验证
        │
Week 8 ──┤
        │ Phase 3 开发中
        │
Week 10──┤
        │
Week 12──┤
        │
Week 14──● Phase 3 完成
        │ 全功能交付，生产环境就绪
```

---

## 8. 风险与缓解措施

### 8.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| LangChain 与 vnpy 依赖冲突 | 高 | 中 | 进程隔离部署，Agent 进程独立 Python 环境 |
| LLM API 调用延迟导致策略信号滞后 | 中 | 高 | 配置触发频率为日频/小时频；设置 LLM 调用超时（30s）；降级策略 |
| RPC 通信延迟导致订单执行延迟 | 高 | 低 | pyzmq 零拷贝特性保证低延迟；本地 localhost 通信延迟 < 1ms |
| LLM 输出不可预测导致错误交易 | 高 | 中 | `with_structured_output` 强制结构化输出；Risk Manager 二次校验；仓位上限硬限制 |
| vnpy 核心框架升级导致插件不兼容 | 中 | 低 | 遵循 vnpy 插件接口规范；仅依赖公开 API，不访问私有成员 |
| 多 Agent 并行调用耗尽 LLM 配额 | 低 | 中 | 支持 Agent 数量可配置；Rate Limiter 控制并发数；支持本地 Ollama 模型 |

### 8.2 业务风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| AI 决策不透明导致合规问题 | 高 | 中 | 每个 Agent 输出 reasoning 字段；完整审计日志；支持"仅信号不执行"模式 |
| 实盘交易中 AI 决策错误导致亏损 | 高 | 中 | 默认关闭自动交易；Risk Manager 硬限制；支持人工审核模式 |
| 用户过度信任 AI 决策 | 中 | 高 | 明确免责声明；UI 中显示 confidence 和 reasoning；提供模拟账户 |
| 数据源更新导致 Agent 决策质量下降 | 中 | 低 | 数据质量监控；多数据源交叉验证告警 |

### 8.3 项目风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| 两个项目分别独立演进，整合版本落后 | 中 | 中 | 最小化对原项目的侵入；定期同步上游更新 |
| 维护成本过高 | 中 | 高 | 清晰的模块边界；完善的自动化测试；文档自动化生成 |
| 社区接受度低 | 低 | 低 | 渐进式发布；先开源核心模块；收集用户反馈迭代 |

---

## 9. 运维与部署方案

### 9.1 部署拓扑

```
┌───────────────────────────────────────────────────────────────────┐
│                        宿主机 (Linux / Windows)                    │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐                 │
│  │ Docker: vnpy-core   │  │ Docker: vnpy-agent  │                 │
│  │ ┌─────────────────┐ │  │ ┌─────────────────┐ │                 │
│  │ │ MainEngine      │ │  │ │ AiHedgeFundEngine│ │                 │
│  │ │ EventEngine     │ │  │ │ LangGraph        │ │                 │
│  │ │ OmsEngine       │ │  │ │ 19 Agents        │ │                 │
│  │ │ Gateways        │ │  │ │ LLM Models       │ │                 │
│  │ │ RpcServer:9001  │◄├──┼─┤ RpcClient:9001   │ │                 │
│  │ │ RpcClient:9002  ├─┼──►│ RpcServer:9002   │ │                 │
│  │ └─────────────────┘ │  │ └─────────────────┘ │                 │
│  │ Port: 9001, 9002   │  │ Port: 9002         │ │                 │
│  └─────────────────────┘  └─────────────────────┘                 │
│                                                                   │
│  ┌─────────────────────┐  ┌─────────────────────┐                 │
│  │ Docker: vnpy-web    │  │ Docker: vnpy-db     │                 │
│  │ ┌─────────────────┐ │  │ ┌─────────────────┐ │                 │
│  │ │ FastAPI:8000    │ │  │ │ PostgreSQL       │ │                 │
│  │ │ React Flow      │ │  │ │ 或 SQLite        │ │                 │
│  │ │ REST API        │ │  │ │ Port: 5432       │ │                 │
│  │ └─────────────────┘ │  │ └─────────────────┘ │                 │
│  │ Port: 3000, 8000   │  │                      │                 │
│  └─────────────────────┘  └─────────────────────┘                 │
│                                                                   │
│  外部依赖:                                                         │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  LLM API (OpenAI/Anthropic/DeepSeek) - 互联网出站             │ │
│  │  交易柜台 (CTP/XTP/IB) - 专线或互联网                         │ │
│  │  数据服务 (RQData/Wind/TuShare) - 互联网                      │ │
│  └─────────────────────────────────────────────────────────────┘ │
└───────────────────────────────────────────────────────────────────┘
```

### 9.2 环境要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 4 核 | 8 核以上 |
| 内存 | 8 GB | 16 GB 以上 |
| 磁盘 | 50 GB | 200 GB SSD（视数据量） |
| 操作系统 | Windows 10+ / Ubuntu 20.04+ | Ubuntu 22.04 LTS |
| Python | 3.11 | 3.13 |
| Docker | 24.0+ | 最新稳定版 |
| 网络 | 可访问互联网（LLM API） | 低延迟专线（交易柜台） |

### 9.3 配置管理

**环境变量（.env）**：

| 变量 | 说明 | 必填 |
|------|------|------|
| VNPY_SETTING_PATH | vnpy 配置文件路径 | 否 |
| AI_AGENT_ENABLED | 是否启用 AI Agent | 否 |
| AI_AGENT_AUTO_TRADE | 是否启用自动交易 | 否 |
| AI_AGENT_TRIGGER_FREQUENCY | 触发频率 | 否 |
| AI_AGENT_SELECTED_ANALYSTS | 选择的分析师 | 否 |
| AI_AGENT_MODEL_NAME | LLM 模型名称 | 否 |
| OPENAI_API_KEY | OpenAI API Key | 条件 |
| FINANCIAL_DATASETS_API_KEY | 备选数据源 Key | 否 |
| RPC_SERVER_PORT | vnpy RPC 端口 | 否 |
| RPC_AGENT_PORT | Agent RPC 端口 | 否 |
| LOG_LEVEL | 日志级别 | 否 |

**配置文件结构**：

| 文件 | 说明 |
|------|------|
| config/default_settings.json | 全局默认配置 |
| config/agent_profiles/value_investing.json | 价值投资 Agent 配置模板 |
| config/agent_profiles/growth_investing.json | 成长投资 Agent 配置模板 |
| config/agent_profiles/macro_trading.json | 宏观交易 Agent 配置模板 |
| config/llm_providers.json | LLM 提供商配置 |

### 9.4 监控与告警

| 监控项 | 指标 | 告警阈值 |
|--------|------|---------|
| Agent 进程状态 | 进程存活 | 进程退出 |
| RPC 连接状态 | 心跳延迟 | 连续 3 次超时（90s） |
| LLM 调用延迟 | P50/P95/P99 延迟 | P95 > 30s |
| LLM 调用成功率 | 成功/失败比 | 成功率 < 90% |
| Agent 决策频率 | 每分钟决策次数 | 偏离预期频率 |
| 订单执行延迟 | 决策到下单时间 | > 5s |
| 内存使用 | Agent 进程内存 | > 2GB |
| 数据库连接 | 活跃连接数 | > 50 |

### 9.5 日志与审计

**审计日志记录内容**：

| 事件 | 记录字段 |
|------|---------|
| Agent 工作流触发 | 时间、触发条件、tickers、选择的分析师 |
| 单个 Agent 执行 | 时间、Agent 名、ticker、输入数据摘要、输出 signal/confidence/reasoning |
| LLM 调用 | 时间、模型名、提供商、Prompt 长度、响应延迟、Token 消耗 |
| Risk Manager 决策 | 时间、波动率指标、仓位限制、VaR |
| Portfolio Manager 决策 | 时间、所有 Agent 信号汇总、允许操作、最终决策 |
| 订单发送 | 时间、ticker、action、quantity、price、order_id |
| 订单状态变化 | 时间、order_id、旧状态、新状态、filled_qty |
| Agent 异常 | 时间、异常类型、消息、堆栈跟踪 |

---

> **文档维护**: 本文档随整合方案迭代更新，由项目架构组负责维护。