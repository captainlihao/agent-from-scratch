# AGENTS.md

## 项目定位

`mini_agent` 是一个**逐步生长的编程 agent**：从最小可用的 agent loop 起步，按需增加工具与能力，目标是能独立完成基础的编程任务（读写改文件、跑命令、跑测试、简单多步任务）。

> 本仓库为多阶段教学仓库，按 git tag `v0.1` → `v1.0` 顺序学习，见 `doc/teaching/`。

设计原则：
- **零第三方依赖**（仅 Python 标准库），保持自包含、易部署。
- **渐进式生长**：每次只加刚好够用的能力，避免过度设计。新功能先在 `AGENTS.md` 记下意图，再落地代码。
- **核心 loop 保持清晰**：agent loop 不加 try/except 兜底，工具失败直接抛异常——保持主路径可读。复杂容错按需在工具层或执行器层引入。

## 当前架构（v0.1）

标准 Python `src/` 包布局：

```
mini_agent/
├── pyproject.toml          # 项目元数据（零第三方依赖）
├── README.md
├── .gitignore
├── src/mini_agent/
│   ├── __init__.py         # 包入口
│   ├── __main__.py         # CLI 入口：python -m mini_agent
│   ├── agent.py            # agent loop：call_llm + agent_loop
│   └── config.py           # BASE_URL/API_KEY/MODEL/MAX_ITERATIONS（硬编码）
├── tests/
│   └── test_loop.py        # import 链路 smoke test
├── examples/               # 示例 IO 文件
└── doc/
    ├── README.txt          # 文档目录说明
    ├── governance/         # 治理文档：约束、规范、决策记录
    ├── plans/               # 计划文档：路线图、功能计划、任务拆解
    ├── operation/          # 操作文档：运行手册、使用指南
    │   └── manual.md       # 操作手册
    └── teaching/           # 教学文档：按版本切片的教程
        ├── README.md       # 教学路径索引
        └── 01-minimal-loop.md
```

- LLM 调用：`http.client` 非流式，OpenAI chat completions 协议。
- **v0.1 无工具**：纯对话循环，LLM 回复不含 `tool_calls` 即结束。
- 迭代上限 `MAX_ITERATIONS = 10`（硬编码，长任务可能静默截断，后续需调）。
- 包未 pip install 时需 `PYTHONPATH=src`；`pip install -e .` 后可免。

## 路线图

按"能完成基础编程工作"倒推，切分为 10 个版本，每版只加一个概念：

- [x] **v0.1 最简 agent loop**：`call_llm`（非流式）+ `agent_loop`（无工具纯对话）+ `__main__` + `config.py`
- [ ] **v0.2 第一个工具**：`Tool`/`ToolRegistry`/`ToolExecutor` + `calculate` + function calling 协议
- [ ] **v0.3 文件读写工具**：`read_file`/`write_file`
- [ ] **v0.4 权限闸门**：`permission.py`（allow/deny/ask 三态）+ `PermissionGate`
- [ ] **v0.5 流式输出**：`call_llm` 改流式 + chunk 拼接 + 打字机效果
- [ ] **v0.6 并发 tool_calls**：`ThreadPoolExecutor` 并发执行同一轮多个 tool_calls
- [ ] **v0.7 系统提示词工程化**：system prompt 从一行扩到完整规范
- [ ] **v0.8 文件操作补全**：`list_dir`、`edit_file`、`grep`
- [ ] **v0.9 shell 执行**：`run_shell` 工具 + 白名单权限
- [ ] **v1.0 上下文管理 + 规划**：message 裁剪/摘要 + `MAX_ITERATIONS` 调大 + plan 引导

> 每加一项，在此打勾并在"当前架构"更新对应模块说明。详细方案见 `doc/plans/teaching-repo-plan.md`。

## 运行

```bash
python -m mini_agent "你的任务"
# 或交互式输入
python -m mini_agent
```

包未安装时需设 `PYTHONPATH=src`（Windows 用 `$env:PYTHONPATH="src"`）；`pip install -e .` 后可从任意目录直接运行。

## 关键约束（踩坑备忘，勿违反）

- **必须用 `http.client`，不能用 `requests`/`urllib`**：`your-gateway-host` 网关对 `Accept-Encoding: gzip` 响应异常返回 502。`call_llm` 里显式设 `Accept-Encoding: identity` 绕过。换 HTTP 客户端会重新踩坑。
- 配置（`BASE_URL`/`API_KEY`/`MODEL`）硬编码在 `config.py`，不从环境变量读。
- agent loop 无 try/except 兜底，工具失败会直接抛异常终止——这是有意为之，保持核心逻辑清晰。
- 迭代上限 `MAX_ITERATIONS = 10`（硬编码）。超限直接返回 `"达到最大迭代次数"`，不报错——长任务可能静默截断。

## 已知行为

- v0.1 无工具：LLM 回复不含 `tool_calls` 即视为完成，agent loop 结束。
- 结束条件：LLM 回复不含 `tool_calls` 即视为完成。
