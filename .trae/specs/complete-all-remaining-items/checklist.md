# Checklist

## 类别一：核心引擎增强
- [x] signal_cooldown 作为 settings 独立可配置项，默认 60 秒
- [x] sma_cross 降级策略：金叉买、死叉卖、否则 hold
- [x] 进度报告：EVENT_AI_STATUS 事件携带 start/progress/complete

## 类别二：RPC 通信增强
- [x] 断线重连：1s/2s/4s/8s 指数退避，最多 5 次
- [x] 心跳：10s 默认间隔，连续 3 次无响应触发重连
- [x] 离线缓冲：deque maxlen=1000，恢复后按序重放

## 类别三：数据适配增强
- [x] get_financial_metrics() 返回 FinancialMetrics 模型列表
- [x] get_company_news() 返回新闻列表
- [x] get_portfolio() 返回完整 Portfolio（positions + account + total_equity）
- [x] _datafeed 属性作为可选扩展点
- [x] get_prices() 日期格式 try/except 保护
- [x] DataAdapter 集成 Cache，TTL 可配置

## 类别四：订单适配增强
- [x] 仓位校验：不允许超卖
- [x] 资金校验：不允许超买
- [x] 价格校验：偏离 >5% 拒绝
- [x] 订单状态 EVENT_ORDER/EVENT_TRADE 通过 RPC 回传

## 类别五：Agent 工作流完善
- [x] 19 个分析师 Agent 移植到 vnpy_ai/agents/，继承 AgentBase
- [x] DecisionResult 转换为 AiSignalData/AiDecisionData 后发布事件
- [x] RPC 消息含 error_code + error_message，自动重试 3 次

## 类别六：Web 后端
- [x] POST /hedge-fund/backtest SSE 流式进度
- [x] /flows GET/POST/PUT/DELETE CRUD
- [x] database/models.py + session.py
- [x] alembic/ 完整迁移链（env.py + alembic.ini + 0001_initial_migration.py）
- [x] repositories: api_key, flow, flow_run
- [x] services: agent, backtest, ollama, graph, portfolio
- [x] routes: api_keys, flow_runs, flows, hedge_fund, language_models, ollama, storage

## 类别七：回测引擎
- [x] engine.py 统一回测入口
- [x] controller.py 资金/滑点/手续费
- [x] trader.py 市价/限价成交模拟
- [x] metrics.py 夏普/Sortino/最大回撤/年化/胜率
- [x] portfolio.py 日频持仓/现金/权益跟踪
- [x] valuation.py 组合估值
- [x] output.py CSV/HTML/matplotlib
- [x] benchmarks.py 基准指数对比
- [x] types.py Pydantic 模型
- [x] vnpy_adapter.py 桥接层

## 类别八：桌面 GUI
- [x] setting_widget.py Agent 参数配置面板
- [x] analyst_selector.py 分析师多选组件
- [x] model_config_widget.py LLM 模型配置面板
- [x] signal_monitor.py AI 信号实时监控面板

## 类别九：运维与部署
- [x] Dockerfile.core/agent/web 补充依赖安装
- [x] GET /health 返回 200 {"status": "ok"}
- [x] setup_structured_logging() stdout JSON 日志
- [x] GET /metrics Prometheus 指标
- [x] send_notification() 邮件/微信推送

## 类别十：文档与工程
- [x] docs/api_reference.md 存在
- [x] docs/migration_guide.md 存在
- [x] examples/notebook/ai_agent_research.ipynb 存在
- [x] CHANGELOG.md 存在
- [x] LICENSE 存在

## 类别十一：测试
- [x] Playwright 冒烟测试脚本存在
- [x] tests/fixtures/mock_agent_outputs.py 存在
- [x] mypy vnpy_ai/ 无错误（Success: no issues found in 69 source files）
- [x] docker compose config YAML 语法有效（Docker CLI 不可用，通过 yaml.safe_load 验证）

## 额外修复
- [x] 修复 3 个被截断的 services 文件（agent_service.py、backtest_service.py、graph.py）
- [x] 修复 2 个被截断的 UI 组件文件（setting_widget.py、analyst_selector.py）
- [x] 修复 mypy.ini 解析错误（多行正则改为单行）
- [x] 修复 84 个 mypy 类型错误（使用泛型 TypeVar 和 cast）
- [x] 修复 utils/progress.py 的 UP017 ruff 错误

## 验证命令
- [x] `pytest tests/ -v` 全部通过（29 passed in 1.86s）
- [x] `mypy vnpy_ai/` 无错误（Success: no issues found in 69 source files）
- [x] `ruff check vnpy_ai/utils/progress.py` 通过（All checks passed!）
- [x] `python -c "from vnpy_ai_web.backend.main import app"` 成功
- [x] `python -c "from vnpy_ai_web.backend.services.agent_service import AgentService"` 成功
