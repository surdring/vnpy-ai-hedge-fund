# Tasks

- [x] Task 1: 修复 P0 Bug — send_decision 返回值
  - [x] 修改 `vnpy_ai/order_adapter.py` L90-L93：取 `vt_orderids[0]` 而非 `str(list)`
  - [x] 验证：`pytest tests/unit/test_order_adapter.py -v`

- [x] Task 2: 修复 P0 Bug — on_market_event 节流与 daily 支持
  - [x] 修改 `vnpy_ai/engine.py` on_market_event：添加 daily 频率支持 + signal_cooldown 节流
  - [x] 验证：`pytest tests/unit/test_engine_workflow.py -v`

- [x] Task 3: 修复 P1 问题（事件常量、配置路径、降级 confidence）
  - [x] 修改 `vnpy_ai/event_adapter.py`：从 `vnpy.trader.event` 导入常量，移除本地定义
  - [x] 修改 `vnpy_ai/config.py`：DEFAULT_CONFIG_PATH 基于 `__file__` 计算
  - [x] 修改 `vnpy_ai/workflow/runner.py`：降级时 confidence=0
  - [x] 验证：`pytest tests/ -v --tb=short`

- [x] Task 4: 新增 Agent 基类
  - [x] 创建 `vnpy_ai/agents/base.py`：AgentBase 类，封装 get_prices/get_financial_metrics/get_company_news/get_portfolio
  - [x] 创建 `tests/unit/test_agent_base.py`：测试数据获取方法
  - [x] 验证：`pytest tests/unit/test_agent_base.py -v`

- [x] Task 5: 新增 LLM 模型工厂
  - [x] 创建 `vnpy_ai/llm/models.py`：从 `ai-hedge-fund/src/llm/` 移植模型工厂，懒加载 langchain
  - [x] 更新 `vnpy_ai/llm/__init__.py`：导出 create_model
  - [x] 验证：`python -c "from vnpy_ai.llm.models import create_model; print(create_model())"` 不报错

- [x] Task 6: 新增内存缓存
  - [x] 创建 `vnpy_ai/data/cache.py`：内存缓存，支持 TTL 配置
  - [x] 创建 `vnpy_ai/data/__init__.py`：导出 Cache
  - [x] 验证：`python -c "from vnpy_ai.data.cache import Cache; c=Cache(ttl=60); c.set('k','v'); assert c.get('k')=='v'"`

- [x] Task 7: 新增工作流节点
  - [x] 创建 `vnpy_ai/workflow/nodes.py`：OrderDispatcher、StatusSync、FallbackHandler
  - [x] 更新 `vnpy_ai/workflow/__init__.py`：导出节点函数
  - [x] 验证：`python -c "from vnpy_ai.workflow.nodes import order_dispatcher, status_sync, fallback_handler"`

- [x] Task 8: 新增 LangGraph 工作流图
  - [x] 创建 `vnpy_ai/workflow/graph.py`：StateGraph 构建，含 Start→Analysts→Risk→Portfolio→OrderDispatcher→End
  - [x] 整合 WorkflowRunner 调用 graph，替换当前降级逻辑
  - [x] 验证：`pytest tests/unit/test_engine_workflow.py -v`

- [x] Task 9: 补充测试覆盖
  - [x] 创建 `tests/unit/test_event_adapter.py`：事件发布测试
  - [x] 创建 `tests/unit/test_engine_workflow.py`：工作流降级路径测试
  - [x] 创建 `tests/integration/test_order_flow.py`：端到端订单流测试
  - [x] 验证：`pytest tests/ -v --tb=short`

- [x] Task 10: 最终验证
  - [x] 运行 `pytest tests/ -v` 确认全部通过（28 passed）
  - [x] 运行 `ruff check vnpy_ai/` 确认无问题（All checks passed!）
  - [x] 确认 `python -c "from vnpy_ai.engine import AiHedgeFundEngine"` 正常导入

# Task Dependencies
- Task 5 依赖 Task 4（LLM 模型工厂需要 Agent 基类的数据方法）
- Task 7 依赖 Task 4（节点需要 Agent 基类）
- Task 8 依赖 Task 5、Task 7（工作流图需要 LLM 模型工厂和节点）
- Task 9 依赖 Task 1-8（测试需要所有功能就绪）
- Task 1、2、3 可并行执行
- Task 4、5、6 可并行执行