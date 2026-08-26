# Changelog

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
