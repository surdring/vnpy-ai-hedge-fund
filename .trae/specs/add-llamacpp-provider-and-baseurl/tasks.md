# Tasks

## 后端变更

- [x] Task 1: llama.cpp 提供商注册与后端支持
  - [x] 1.1 在 `config/llm_providers.json` 中新增 llama.cpp 条目（local: true, 默认 base_url: `http://localhost:8080/v1`）
  - [x] 1.2 在 `vnpy_ai/llm/models.py` 的 `create_model()` 中新增 `llamacpp` provider 分支，使用 `ChatOpenAI` + 自定义 base_url（OpenAI 兼容模式）
  - [x] 1.3 在 `vnpy_ai/llm/models.py` 的 `get_available_providers()` 中新增 `llamacpp` 检测（依赖 `langchain_openai`）
  - [x] 1.4 在 `ai-hedge-fund/src/llm/models.py` 的 `ModelProvider` 枚举中新增 `LLAMA_CPP = "llama.cpp"`，并在 `get_model()` 中新增对应分支
  - 验证：通过代码审查确认所有修改正确

- [x] Task 2: base_url 传递链路打通
  - [x] 2.1 在 `vnpy_ai/config.py` 的 `AiSettings` 中新增 `llm_base_url: str = ""` 字段
  - [x] 2.2 修改 `vnpy_ai/llm/models.py` 的 `create_model()`，确保所有 provider 分支都能接收并优先使用 `base_url` kwargs（确认所有 provider 通过 `**kwargs` 传递）
  - [x] 2.3 修改 `vnpy_ai/utils/llm.py` 的 `call_llm()` 和新增 `_extract_base_url()`，将 state 中的 `base_url` 传递到 `create_model()` 调用
  - 验证：通过代码审查确认 base_url 传递链路完整

- [x] Task 3: Qt 桌面端 base_url 编辑
  - [x] 3.1 在 `vnpy_ai/ui/model_config_widget.py` 的 `ModelConfigWidget` 中新增 `base_url_edit` 输入框
  - [x] 3.2 更新 `get_config()` 和 `set_config()` 方法，包含 `base_url` 字段
  - 验证：通过代码审查确认

## 前端变更

- [x] Task 4: Web 前端 base_url 编辑区
  - [x] 4.1 在 `vnpy_ai_web/frontend/src/components/settings/api-keys.tsx` 中为每个 LLM 提供商新增 `base_url` 输入框
  - [x] 4.2 新增 `LLM_BASE_URLS` 配置常量列表（10 个提供商，含默认值和占位提示）
  - [x] 4.3 后端复用现有 `api_keys` 路由进行 `base_url` 持久化（无需新增 API）
  - 验证：TypeScript 类型检查通过（`npx tsc --noEmit`）

- [x] Task 5: Web 前端本地模型标签页新增 llama.cpp
  - [x] 5.1 在 `models.tsx` 的本地模型标签页中新增 llama.cpp 图标/选项（`Cpu` 图标，与 Ollama 并列）
  - [x] 5.2 创建 `llamacpp-settings.tsx` 组件，展示 llama.cpp 状态信息（服务地址、连接状态、模型列表）
  - [x] 5.3 后端新增 `GET /llamacpp/status` 状态检测 API（检测 `http://localhost:8080/v1/models` 端点）
  - 验证：通过代码审查确认

# Task Dependencies
- Task 2 依赖 Task 1（llama.cpp 也需要 base_url 传递）
- Task 3 可与 Task 1、Task 2 并行
- Task 4 依赖 Task 2（需要后端 base_url 传递链路）
- Task 5 依赖 Task 1（需要 llama.cpp 后端支持）
- Task 4 和 Task 5 可并行执行