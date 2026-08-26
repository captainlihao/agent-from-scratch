# Changelog

## [v0.2] - 第一个工具

### Added
- `src/mini_agent/tools/base.py`：`Tool`/`ToolRegistry`/`ToolExecutor` 三件套
- `src/mini_agent/tools/calc.py`：`calculate` 工具（数学表达式计算，正则白名单防注入）
- `src/mini_agent/tools/__init__.py`：注册中心，创建 registry + executor 并注册 calculate
- `tests/test_tools.py`：工具 smoke test（registry/calculate/异常处理）
- `doc/teaching/02-first-tool.md`：第二课教学文档

### Changed
- `src/mini_agent/agent.py`：`call_llm` 加 `tools` 参数（function calling 协议）；`agent_loop` 加 tool_calls 执行 + `role=tool` 回灌
- `src/mini_agent/__main__.py`：system prompt 改为"你是一个助手，通过调用工具完成任务"

### Why
- 引入 OpenAI function calling 协议，让 LLM 能真正"做事"而不只是聊天。
- Tool 三件套（定义/注册/执行）分离关注点，后续加工具只需写 handler + 注册，不动 loop。
- Executor 捕获 handler 异常返回错误信息给 LLM，让 LLM 决定重试或告知用户——容错在工具层，不在 loop 层。

## [v0.1] - 最简 agent loop

### Added
- `src/mini_agent/agent.py`：`call_llm`（非流式）+ `agent_loop`（无工具纯对话循环）
- `src/mini_agent/__main__.py`：CLI 入口，支持单次任务模式和交互模式
- `src/mini_agent/config.py`：`BASE_URL`/`API_KEY`/`MODEL`/`MAX_ITERATIONS`（硬编码）
- `src/mini_agent/__init__.py`：包入口
- `tests/test_loop.py`：import 链路 smoke test
- `doc/teaching/01-minimal-loop.md`：第一课教学文档
- `doc/teaching/README.md`：教学路径索引
- `doc/plans/teaching-repo-plan.md`：多阶段教学仓库完整方案
- `doc/operation/manual.md`：操作手册（v0.1 版）

### Why
- 从最小可用的对话 loop 起步，先讲清"什么是 agent loop"：messages 列表、调 LLM、判断结束条件。
- 不引入工具、权限、流式、并发，让第一课的 loop 概念最干净。
- `http.client` + `Accept-Encoding: identity` 是踩坑后的选择（网关对 gzip 响应异常），从第一版就确立。
