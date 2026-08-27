# Changelog

## [v0.8] - 文件操作补全

### Added
- `src/mini_agent/tools/file.py`：新增 `edit_file`（精确字符串替换，多匹配安全检查）、`list_dir`（目录列举，200 条上限）、`grep`（正则搜索，100 条上限，纯标准库 `re`+`os.walk`+`fnmatch`）
- `docs/tutorials/08-file-operations.md`：第八课教学文档

### Changed
- `src/mini_agent/tools/file.py`：`read_file` 加 `offset`/`limit` 分段读取 + 行号前缀（`00001| `）+ 剩余行提示
- `src/mini_agent/permission.py`：`list_dir`/`grep` 走 ALLOW，`edit_file` 走 ASK
- `src/mini_agent/tools/__init__.py`：注册 6 个工具
- `tests/test_tools.py`：从 8 个测试扩到 15 个（新增 read_file offset/limit、edit_file 单次/无匹配/多匹配、list_dir、grep 有匹配/无匹配）

### Why
- v0.3 只有 read_file/write_file，agent 看不到目录结构、改文件只能整文件重写、找不到内容在哪——补齐 list_dir/edit_file/grep 形成完整操作链路。
- `edit_file` 用字符串匹配而非行号编辑：LLM 容易数错行号，从 read_file 输出复制原文更可靠。多匹配时报错而非静默替换第一处，防误改。
- `read_file` 加 offset/limit：大文件不爆上下文；行号前缀帮 LLM 定位 edit_file 的 old_string。
- `grep` 用纯标准库而非 ripgrep：零第三方依赖约定。性能差但教学场景够用，v0.9 加 run_shell 后 LLM 可自己调 rg。
- 不做 OpenCode 的 8 种模糊匹配策略、输出临时文件、文件锁、LSP 集成——对教学项目过度设计。

## [v0.7] - 系统提示词工程化

### Added
- `src/mini_agent/prompt.py`：`build_system_prompt(agent_name)` 分层组装（header 身份 + `_CORE_RULES` 行为规范 + `environment` 环境信息）；`_detect_git` 纯目录遍历判断 git 仓库
- `tests/test_prompt.py`：system prompt smoke test（组装/ header / 回退/ 环境字段）
- `docs/tutorials/07-system-prompt.md`：第七课教学文档

### Changed
- `src/mini_agent/__main__.py`：`messages[0]` 从一行硬编码字符串改为调用 `build_system_prompt()`

### Why
- 一行 system prompt 缺环境信息（工作目录/平台/日期），模型靠猜路径和命令易出错。
- 无行为规范，模型可能啰嗦、加 emoji、复述工具输出、主动总结——多轮迭代时污染上下文。
- 分层组装（header/core_rules/environment）借鉴 OpenCode 四层结构做减法：去掉 provider 适配（单模型）和 custom 加载（留 v0.8）。
- `header(agent_name)` 为多 agent/sub-agent 预留接口，当前只实现 build，后续加 explore/plan 只需在 dict 加一行。
- `agent.py` 不动——核心 loop 仍只认 messages 列表，prompt 构造是入口层职责，保持 loop 清晰。

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
- `docs/tutorials/04-permission-gate.md`：第四课教学文档

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
- `docs/tutorials/03-file-tools.md`：第三课教学文档

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
- `docs/tutorials/02-first-tool.md`：第二课教学文档

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
- `docs/tutorials/01-minimal-loop.md`：第一课教学文档
- `docs/tutorials/README.md`：教学路径索引
- `docs/plans/teaching-repo-plan.md`：多阶段教学仓库完整方案
- `docs/operation/manual.md`：操作手册（v0.1 版）

### Why
- 从最小可用的对话 loop 起步，先讲清"什么是 agent loop"：messages 列表、调 LLM、判断结束条件。
- 不引入工具、权限、流式、并发，让第一课的 loop 概念最干净。
- `http.client` + `Accept-Encoding: identity` 是踩坑后的选择（网关对 gzip 响应异常），从第一版就确立。
