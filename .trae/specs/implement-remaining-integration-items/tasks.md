# Tasks

## P0：核心决策链路打通（阻塞项）

- [x] Task 1: 创建 tools/ 和 utils/ 目录基础（P2 前置依赖）
  - [x] 创建 `vnpy_ai/tools/__init__.py` 和 `vnpy_ai/tools/api.py`，从 `ai-hedge-fund/src/tools/api.py` 移植核心数据获取函数，适配为通过 DataAdapter 获取数据
  - [x] 创建 `vnpy_ai/utils/__init__.py`、`analysts.py`、`api_key.py`、`llm.py`、`display.py`、`progress.py`、`visualize.py`，从 upstream 移植并适配 import 路径
  - [x] 验证：`python -c "from vnpy_ai.tools.api import get_financial_metrics; from vnpy_ai.utils.llm import call_llm"`

- [x] Task 2: 扩展 LLM Provider 到 14 个
  - [x] 修改 `vnpy_ai/llm/models.py`：新增 Alibaba、DeepSeek、Groq、Kimi、Meta、Mistral、OpenRouter、GigaChat、xAI 共 10 个 provider，每个使用对应 langchain_* 包，导入失败时优雅降级
  - [x] 移植 `ai-hedge-fund/src/llm/api_models.json` 和 `ollama_models.json` 到 `vnpy_ai/llm/`
  - [x] 验证：`python -c "from vnpy_ai.llm.models import get_available_providers; assert len(get_available_providers()) >= 4"`

- [x] Task 3: 实现 19 个分析师 Agent 真实 LLM 调用
  - [x] 从 `ai-hedge-fund/src/agents/` 移植每个分析师的核心分析逻辑（如 warren_buffett 的 `analyze_fundamentals`、`analyze_consistency`、`analyze_moat` 等）
  - [x] 适配为继承 `AgentBase` 的类方法，通过 `self.get_prices()` / `self.get_financial_metrics()` 获取数据，通过 `vnpy_ai.utils.llm.call_llm()` 调用 LLM
  - [x] 使用 Pydantic 模型定义结构化输出（如 `WarrenBuffettSignal`），强制 LLM 返回 signal/confidence/reasoning
  - [x] 涉及文件：`warren_buffett.py`、`benjamin_graham.py`、`bill_ackman.py`、`cathie_wood.py`、`charlie_munger.py`、`michael_burry.py`、`mohnish_pabrai.py`、`nassim_taleb.py`、`peter_lynch.py`、`phil_fisher.py`、`rakesh_jhunjhunwala.py`、`stanley_druckenmiller.py`、`aswath_damodaran.py`、`growth_agent.py`、`news_sentiment.py`、`fundamentals.py`、`sentiment.py`、`technicals.py`、`valuation.py`
  - [x] 验证：`pytest tests/unit/test_agent_base.py -v`（新增测试验证 analyze 返回结构化信号）

- [x] Task 4: 实现顶层 Risk Manager
  - [x] 创建 `vnpy_ai/agents/risk_manager.py`，定义 `RiskManagerAgent(AgentBase)` 类
  - [x] 从 `ai-hedge-fund/src/agents/risk_manager.py` 移植 `calculate_volatility_metrics`、`calculate_var`、`calculate_correlation_analysis` 等核心函数
  - [x] 实现 `analyze()` 方法：计算每个 ticker 的波动率、VaR、相关性，返回仓位限制和风控评估
  - [x] 验证：`python -c "from vnpy_ai.agents.risk_manager import RiskManagerAgent"`

- [x] Task 5: 实现顶层 Portfolio Manager
  - [x] 创建 `vnpy_ai/agents/portfolio_manager.py`，定义 `PortfolioManagerAgent(AgentBase)` 类
  - [x] 从 `ai-hedge-fund/src/agents/portfolio_manager.py` 移植 `PortfolioManagerOutput`、`PortfolioDecision` 模型和决策逻辑
  - [x] 实现 `analyze()` 方法：综合分析师信号和风控评估，通过 LLM 生成最终 buy/sell/short/cover/hold 决策
  - [x] 验证：`python -c "from vnpy_ai.agents.portfolio_manager import PortfolioManagerAgent"`

- [x] Task 6: 工作流图替换占位符为真实节点
  - [x] 修改 `vnpy_ai/workflow/graph.py`：用 `RiskManagerAgent` 和 `PortfolioManagerAgent` 实例替换 `_make_risk_manager_node()` 和 `_make_portfolio_manager_node()` 内联占位符
  - [x] 确保工作流拓扑：Start → Analysts → RiskManager → PortfolioManager → OrderDispatcher → StatusSync → End
  - [x] 验证：`pytest tests/unit/test_engine_workflow.py -v`

## P1：回测引擎与 GUI

- [x] Task 7: 实现 BacktestEngine 真实回测逻辑
  - [x] 修改 `vnpy_ai/backtesting/engine.py`：`run()` 方法通过 `VnpyAdapter.load_bars()` 加载数据，调用 `BacktestController` 模拟交易，通过 `metrics.py` 计算绩效
  - [x] 返回包含 status、metrics（夏普/Sortino/最大回撤/年化收益）、trades 列表的完整结果
  - [x] 验证：`pytest tests/ -v -k backtest`

- [x] Task 8: 实现 VnpyAdapter 数据加载
  - [x] 修改 `vnpy_ai/backtesting/vnpy_adapter.py`：`load_bars()` 通过 `MainEngine` 获取数据库接口，调用 `load_bar_data()` 加载历史 BarData
  - [x] 正确构造查询参数：从 ticker 解析 symbol/exchange，设置 interval 和 start/end datetime
  - [x] 验证：`python -c "from vnpy_ai.backtesting.vnpy_adapter import VnpyAdapter"`

- [x] Task 9: vnpy GUI 新增 AI Agent 菜单
  - [x] 修改 `vnpy/trader/ui/mainwindow.py`：新增 "AI Agent" 菜单，含 "启动 AI 对冲基金"、"配置 Agent"、"信号监控" 子菜单项
  - [x] 子菜单项触发 `AiHedgeFundApp` 的相应功能（通过 MainEngine.get_engine 获取 AiHedgeFundEngine）
  - [x] 验证：`python -c "from vnpy.trader.ui.mainwindow import MainWindow"`

## P2：Web 后端与 UI 组件

- [x] Task 10: Web 后端 services 替换 stub
  - [x] 修改 `vnpy_ai_web/backend/services/graph.py`：调用 `vnpy_ai.workflow.graph.build_workflow_graph` 构建工作流
  - [x] 修改 `vnpy_ai_web/backend/services/agent_service.py`：调用 `vnpy_ai.agents.catalog` 获取 Agent 元数据
  - [x] 修改 `vnpy_ai_web/backend/services/backtest_service.py`：调用 `vnpy_ai.backtesting.engine.BacktestEngine` 执行回测
  - [x] 验证：`python -c "from vnpy_ai_web.backend.services.graph import build_graph"`

- [x] Task 11: UI 组件实现真实 PySide6 界面
  - [x] 修改 `vnpy_ai/ui/setting_widget.py`：实现 Agent 参数配置面板（触发频率、分析师选择、LLM 模型、仓位上限、自动交易开关）
  - [x] 修改 `vnpy_ai/ui/analyst_selector.py`：实现 QListWidget with checkboxes 的分析师多选组件
  - [x] 修改 `vnpy_ai/ui/model_config_widget.py`：实现 LLM 模型配置面板（provider 下拉、model 名称、temperature 滑块）
  - [x] 修改 `vnpy_ai/ui/signal_monitor.py`：实现 QTableWidget 显示最近信号和决策（ticker、agent、signal、confidence、timestamp）
  - [x] 验证：`python -c "from vnpy_ai.ui.setting_widget import SettingWidget"`

## P3：非阻塞项

- [x] Task 12: 实现 add_ai_agent() 方法
  - [x] 修改 `vnpy/trader/engine.py`：`MainEngine` 新增 `add_ai_agent(agent_class)` 方法，作为 `add_app()` 的语义化别名
  - [x] 验证：`python -c "from vnpy.trader.engine import MainEngine; assert hasattr(MainEngine, 'add_ai_agent')"`

- [x] Task 13: 修复测试环境目录
  - [x] 创建 `tests/conftest.py` 或修改现有 conftest，在测试收集前自动创建 `C:\Users\DELL\.vntrader\log\` 目录
  - [x] 验证：`pytest tests/ -v --collect-only`（无目录缺失错误）

# Task Dependencies

- Task 1（tools/utils）是 Task 3（Agent 实现）的前置依赖，因 Agent 需调用 `utils.llm.call_llm`
- Task 2（LLM 扩展）是 Task 3 和 Task 5 的前置依赖，因 Agent 和 Portfolio Manager 需通过 LLM 调用
- Task 3、4、5 可并行执行（均依赖 Task 1、2）
- Task 6 依赖 Task 4、5（需 RiskManagerAgent 和 PortfolioManagerAgent 类）
- Task 7 依赖 Task 8（BacktestEngine 需 VnpyAdapter 加载数据）
- Task 9、10、11、12、13 无依赖，可并行执行
- **并行执行策略**：
  - 第一批：Task 1、Task 2（基础工具）
  - 第二批：Task 3、Task 4、Task 5、Task 8、Task 9、Task 10、Task 11、Task 12、Task 13（并行）
  - 第三批：Task 6、Task 7（依赖前批）
