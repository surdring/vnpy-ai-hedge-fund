# 添加 llama.cpp 本地 LLM 提供商 + 全局 base_url 编辑支持

## Why
当前系统仅支持 Ollama 作为本地 LLM 提供商。llama.cpp 是另一个广泛使用的本地推理引擎，通过其内置的 HTTP server 提供 OpenAI 兼容 API。同时，所有 LLM 提供商的 `base_url` 目前仅可通过环境变量静态配置，缺乏前端可视化编辑能力。

## What Changes
- 新增 **llama.cpp** 作为本地 LLM 提供商选项，与 Ollama 并列
- 为**所有 LLM 提供商**（Ollama、OpenAI、DeepSeek、Anthropic、Google、llama.cpp 等）在前端设置页面添加 `base_url` 编辑输入框
- 在 Qt 桌面端 `ModelConfigWidget` 中也添加 `base_url` 编辑字段
- 后端 `AiSettings` 模型新增 `llm_base_url` 字段
- 后端的 `create_model()` 和 `get_model()` 支持通过 `base_url` 参数覆盖默认地址

## Impact
- Affected specs: 无（全新功能）
- Affected code:
  - `config/llm_providers.json` — 新增 llama.cpp 条目
  - `vnpy_ai/llm/models.py` — 新增 llama.cpp provider 处理；所有 provider 支持传入 base_url
  - `ai-hedge-fund/src/llm/models.py` — `ModelProvider` 枚举新增 `LLAMA_CPP`
  - `vnpy_ai/config.py` — `AiSettings` 新增 `llm_base_url` 字段
  - `vnpy_ai/ui/model_config_widget.py` — Qt 组件新增 `base_url` 输入框
  - `vnpy_ai_web/frontend/src/components/settings/api-keys.tsx` — 新增 `base_url` 编辑区
  - `vnpy_ai_web/frontend/src/components/settings/models.tsx` — 本地模型标签页新增 llama.cpp 选项
  - `vnpy_ai_web/frontend/src/components/settings/models/ollama.tsx` — 重命名或新增 llama.cpp 设置组件

## ADDED Requirements

### Requirement: llama.cpp 本地 LLM 提供商
系统 SHALL 支持 llama.cpp 作为本地 LLM 提供商，通过其 HTTP Server 的 OpenAI 兼容 API 进行调用。

#### Scenario: 用户选择 llama.cpp 作为本地模型提供商
- **WHEN** 用户在设置页面选择 llama.cpp 作为本地模型
- **THEN** 系统使用 OpenAI 兼容客户端连接 llama.cpp 的 HTTP server（默认 `http://localhost:8080/v1`）
- **AND** 用户可以自定义 base_url

#### Scenario: llama.cpp 在本地模型列表中显示
- **WHEN** 用户打开设置 → Models → 本地模型标签页
- **THEN** llama.cpp 与 Ollama 并列显示为可选的本地推理引擎

### Requirement: 所有 LLM 提供商支持 base_url 编辑
系统 SHALL 为所有 LLM 提供商提供 base_url 前端编辑能力，允许用户覆盖默认 API 端点地址。

#### Scenario: 用户在设置页面编辑 base_url
- **WHEN** 用户在 API Keys 设置区域为某个提供商输入自定义 base_url
- **THEN** 该 base_url 被持久化保存
- **AND** 后续 LLM 调用使用该自定义 base_url 而非默认值

#### Scenario: 用户不为 base_url 提供值
- **WHEN** 用户将 base_url 留空
- **THEN** 系统使用该提供商的默认 base_url

#### Scenario: Qt 桌面端也支持 base_url 编辑
- **WHEN** 用户在 VeighNa 桌面端的 LLM 配置面板中
- **THEN** 可以看到并编辑 base_url 字段