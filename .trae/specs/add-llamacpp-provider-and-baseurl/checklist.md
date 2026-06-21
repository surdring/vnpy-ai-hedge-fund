# Checklist

- [x] `config/llm_providers.json` 包含 llama.cpp 条目，`local: true`
- [x] `vnpy_ai/llm/models.py` 的 `create_model()` 支持 `llamacpp` provider（OpenAI 兼容模式，默认 `http://localhost:8080/v1`）
- [x] `vnpy_ai/llm/models.py` 的 `get_available_providers()` 包含 `llamacpp`
- [x] `ai-hedge-fund/src/llm/models.py` 的 `ModelProvider` 枚举包含 `LLAMA_CPP`
- [x] `ai-hedge-fund/src/llm/models.py` 的 `get_model()` 支持 `LLAMA_CPP` 分支
- [x] `vnpy_ai/config.py` 的 `AiSettings` 包含 `llm_base_url` 字段
- [x] `vnpy_ai/llm/models.py` 的 `create_model()` 所有 provider 分支都正确处理 `base_url` kwargs
- [x] `vnpy_ai/utils/llm.py` 的 `call_llm()` 正确传递 `base_url` 到 `create_model()`
- [x] `vnpy_ai/ui/model_config_widget.py` 包含 `base_url` 输入框
- [x] `ModelConfigWidget.get_config()` 和 `set_config()` 包含 `base_url` 字段
- [x] Web 前端 `api-keys.tsx` 为每个 LLM 提供商展示 `base_url` 编辑输入框
- [x] 后端提供 `base_url` 持久化 API（CRUD）
- [x] Web 前端本地模型标签页包含 llama.cpp 选项
- [x] `llamacpp-settings.tsx` 组件存在并展示 llama.cpp 状态
- [x] 后端提供 llama.cpp 状态检测 API
- [x] llama.cpp 选择后，LLM 调用能正确连接到用户指定的 base_url