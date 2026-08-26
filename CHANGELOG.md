# Changelog

## [v0.6] - 并发 tool_calls

### Changed
- `src/mini_agent/agent.py`：`agent_loop` 里 tool_calls 执行从串行 for 循环改为 `ThreadPoolExecutor` 并发；`pool.map` 保证结果按原序回灌

### Why
- 同一轮的多个 tool_calls 互不依赖，串行执行浪费时间。
- `ThreadPoolExecutor` 是"最小改动 + 足够好的并发"——不需要把整个调用链 async 化。
- `pool.map` 保证结果顺序与 tool_calls 原序一致，回灌顺序安全。
- v0.4 的 `_ask_lock` 在并发场景生效：防止多个 ASK 权限交互交错。

## [v0.5] - 流式输出

### Changed
- `src/mini_agent/agent.py`：`call_llm` 改流式（`stream=True` + SSE 解析 + chunk 拼接 + 打字机效果）；`agent_loop` 里 print 标记移到 `call_llm` 之前

### Why
- 非流式下 LLM 全部想完才返回，长回复时终端有明显等待。
- 流式边收边显示，打字机效果让用户体感更快。
- `http.client` + `Accept-Encoding: identity` 保证收到未压缩的原始文本流，逐行解析可靠。
- tool_calls 的 arguments 跨 chunk 拼接（`+=`），用 index 聚合——流式下结构化数据的处理方式。

## [v0.4] - 权限闸门

### Added
- `src/mini_agent/permission.py`：`PermissionPolicy`（allow/deny/ask 三态）+ `PermissionGate`（检查+交互+锁）
- `doc/teaching/04-permission-gate.md`：第四课教学文档

### Changed
- `src/mini_agent/tools/base.py`：`ToolExecutor` 加 `gate` 参数，`execute` 里先过 `gate.guard` 再调 handler
- `src/mini_agent/tools/__init__.py`：import PermissionGate（executor 自动创建默认 gate）
- `tests/test_tools.py`：write_file 用放行策略绕过 ASK；新增 DENY 策略测试

### Why
- v0.3 的 write_file 直接执行不问人，有覆盖重要文件的风险。
- 三态（allow/deny/ask）覆盖"总是允许/总是禁止/看情况"三种现实需求，比两态更灵活。
- 拒绝不是报错而是工具结果，回灌给 LLM 让它调整策略——容错在工具层。
- `_ask_lock` 为 v0.6 并发 tool_calls 预留，防止多个权限提示交错。

## [v0.3] - 文件读写工具

### Added
- `src/mini_agent/tools/file.py`：`read_file`/`write_file` 工具
- `examples/input.txt`、`examples/input2.txt`：示例文件
- `doc/teaching/03-file-tools.md`：第三课教学文档

### Changed
- `src/mini_agent/tools/__init__.py`：注册 read_file/write_file
- `tests/test_tools.py`：加 read_file/write_file 测试

### Why
- agent 不改文件没法做编程任务，文件读写是基础能力。
- 先让"能写文件"跑通，权限是独立概念，v0.4 专门讲。
- 加工具只需写 handler + 注册，不动 agent.py——验证三件套分离关注点的好处。

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
