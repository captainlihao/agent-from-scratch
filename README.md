<div align="center">

# agent-from-scratch

### 逐步生长的编程 Agent · 从零开始构建一个能干活的 AI Agent

A step-by-step tutorial for building a coding agent from scratch — in incremental versions (v0.1 → ongoing).

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Dependencies](https://img.shields.io/badge/dependencies-zero-green)](#)
[![Versions](https://img.shields.io/badge/versions-v0.1%E2%86%92ongoing-orange)](#学习路径)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](./LICENSE)

**[English](./README_EN.md)** · **中文**

</div>

---

> **这是什么**：一个按 git tag 切片的教学仓库。从最小可用的 agent loop（v0.1，无工具纯对话）起步，每个版本**只引入一个新概念**，一路长到能读写文件、跑命令、跑测试的编程 agent（持续迭代，不设上限）。
>
> **适合谁**：想搞清楚 LLM agent 到底怎么转起来的开发者。不调框架、不装 LangChain，只用 Python 标准库从零搭。

## 为什么用这个仓库学 Agent

- **零第三方依赖** —— 全程只用 Python 标准库（`http.client` / `json` / `concurrent.futures`），不装 LangChain、不装 requests。代码自包含，每一行都能读懂。
- **版本切片，每版只加一个概念** —— `git diff v0.1..v0.2` 就是"加一个工具"的全部改动，diff 可读，学习负担低。版本持续递增，不设上限。
- **真实可跑的 agent** —— 不是玩具 demo：支持 function calling、流式输出、权限闸门、并发工具调用，能真的读写文件、跑命令。
- **配套中文教程** —— 每个版本一份教学文档（`docs/tutorials/`），讲清"为什么这么设计"，不只是贴代码。
- **渐进式生长的设计哲学** —— 演示一个 agent 项目如何从 50 行长到生产可用，每一步的取舍都有据可查。

## 快速开始

```bash
# 1. 克隆
git clone https://github.com/liiiiiiiiil/agent-from-scratch.git
cd agent-from-scratch

# 2. 配置 LLM 网关
cp src/mini_agent/config_example.py src/mini_agent/config_local.py
#    编辑 config_local.py 填入你的 BASE_URL / API_KEY / MODEL（此文件不进 git）

# 3. 安装（二选一）
pip install -e .                 # 开发模式，推荐
$env:PYTHONPATH="src"           # 免安装，PowerShell；bash 用 PYTHONPATH=src

# 4. 跑起来
python -m mini_agent "帮我算一下 123 * 456"
python -m mini_agent             # 或交互式输入
```

> 需要 Python 3.9+（用了 `dict[str, ...]` 等新语法）。

## 学习路径

按 `v0.1 → v0.X` 顺序 checkout，每版配套一份教程。**这是本仓库的核心**。

| 版本 | 主题 | 每版只加一个概念 | 教程 |
|---|---|---|---|
| **v0.1** | 最简 agent loop | `call_llm` + `agent_loop`（无工具纯对话） | [01-minimal-loop.md](./docs/tutorials/01-minimal-loop.md) |
| **v0.2** | 第一个工具 | `Tool`/`ToolRegistry` + `calculate` + function calling | [02-first-tool.md](./docs/tutorials/02-first-tool.md) |
| **v0.3** | 文件读写工具 | `read_file` / `write_file` | [03-file-tools.md](./docs/tutorials/03-file-tools.md) |
| **v0.4** | 权限闸门 | `permission.py`（allow/deny/ask 三态） | [04-permission-gate.md](./docs/tutorials/04-permission-gate.md) |
| **v0.5** | 流式输出 | `call_llm` 改流式 + 打字机效果 | [05-streaming.md](./docs/tutorials/05-streaming.md) |
| **v0.6** | 并发 tool_calls | `ThreadPoolExecutor` 并发执行 | [06-concurrent-tool-calls.md](./docs/tutorials/06-concurrent-tool-calls.md) |
| **v0.7** | 系统提示词工程化 | system prompt 从一行扩到完整规范 | [07-system-prompt.md](./docs/tutorials/07-system-prompt.md) |
| **v0.8** | 文件操作补全 | `list_dir` / `edit_file` / `grep` | [08-file-operations.md](./docs/tutorials/08-file-operations.md) |
| **v0.9** | 权限系统升级 | 二维权限 (tool_name, pattern) + fnmatch 通配符匹配 | [09-permission-upgrade.md](./docs/tutorials/09-permission-upgrade.md) |
| v0.10 | shell 执行 | `run_shell` 工具 + BashArity 命令泛化 | _待落地_ |
| v0.11 | 上下文管理 | message 裁剪/摘要 + `MAX_ITERATIONS` 调大 | _待落地_ |
| v0.12 | plan 引导 | 规划模式引导 | _待落地_ |
| ... | ... | ...（持续迭代，按需追加） | ... |

**如何切版本学习：**

```bash
git tag                    # 看所有版本
git checkout v0.1          # 切到第一版
# 读 docs/tutorials/01-minimal-loop.md
# 跑教程里的命令
git checkout v0.2          # 看差异：git diff v0.1..v0.2
# 读 02-first-tool.md ... 依次到最新版
```

## 项目结构

```
mini_agent/
├── src/mini_agent/
│   ├── agent.py            # agent loop：call_llm + agent_loop
│   ├── config.py           # 配置占位 + 自动加载 config_local.py
│   ├── config_example.py   # 配置模板（复制为 config_local.py 使用）
│   ├── permission.py       # 权限闸门：allow/deny/ask 三态
│   └── tools/
│       ├── base.py         # Tool / ToolRegistry / ToolExecutor
│       ├── calc.py         # calculate 工具
│       └── file.py         # read_file / write_file 工具
├── tests/                  # smoke tests
├── docs/
│   ├── tutorials/          # 按版本切片的教程（核心）
│   ├── plans/              # 路线图、功能计划
│   ├── operation/          # 运行手册、使用指南
│   └── governance/         # 治理文档、决策记录
└── examples/               # 示例 IO 文件
```

## 设计哲学

- **渐进式生长**：每次只加刚好够用的能力，避免过度设计。新功能先在 `AGENTS.md` 记下意图，再落地代码。
- **核心 loop 保持清晰**：agent loop 不加 try/except 兜底，工具失败直接抛异常——保持主路径可读。复杂容错按需在工具层引入。
- **零依赖**：只用标准库，保持自包含、易部署。换 HTTP 客户端会踩坑（见 `AGENTS.md` 关键约束）。

## 文档

- [教学路径索引](./docs/tutorials/README.md) —— **从这里开始学**
- [完整使用手册](./docs/operation/manual.md) —— 最新版全量用法、配置、FAQ
- [路线图与计划](./docs/plans/teaching-repo-plan.md) —— 版本切分方案
- [AGENTS.md](./AGENTS.md) —— 项目架构与约束备忘

## 贡献

欢迎提 Issue / PR。如果是新增版本切片，请先读 `docs/plans/teaching-repo-plan.md` 和 `AGENTS.md`，遵循"每版只加一个概念"的切分原则。

## License

MIT — 见 [LICENSE](./LICENSE)

---

<div align="center">

**如果这个仓库对你有帮助，欢迎 Star ⭐ 让更多人看到。**

</div>

<!-- 关键词 / Keywords: agent tutorial, agent 教程, LLM agent, coding agent, Python agent, function calling, 从零构建 agent, AI agent, 大模型 agent, agent loop, tool calling -->
