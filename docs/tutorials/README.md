# 教学路径（tutorials）

本目录是 `mini_agent` 教学仓库的核心：按版本号切片的教程文档。

## 学习顺序

`v0.1 → v0.2 → ... → v0.X`（持续迭代，不设上限），每版配套一份文档，每版只引入一个新概念。

| 版本 | 主题 | 文档 |
|---|---|---|
| v0.1 | 最简 agent loop | [01-minimal-loop.md](01-minimal-loop.md) |
| v0.2 | 第一个工具 | [02-first-tool.md](02-first-tool.md) |
| v0.3 | 文件读写工具 | [03-file-tools.md](03-file-tools.md) |
| v0.4 | 权限闸门 | [04-permission-gate.md](04-permission-gate.md) |
| v0.5 | 流式输出 | [05-streaming.md](05-streaming.md) |
| v0.6 | 并发 tool_calls | [06-concurrent-tool-calls.md](06-concurrent-tool-calls.md) |
| v0.7 | 系统提示词工程化 | [07-system-prompt.md](07-system-prompt.md) |
| v0.8 | 文件操作补全 | [08-file-operations.md](08-file-operations.md) |
| v0.9 | 权限系统升级 | 09-permission-upgrade.md（待落地） |
| v0.10 | shell 执行 | 10-shell-execution.md（待落地） |
| v0.11 | 上下文管理 | 11-context-management.md（待落地） |
| v0.12 | plan 引导 | 12-plan-guidance.md（待落地） |
| ... | ... | ...（按需追加） |

## 环境准备（一次性）

1. **Python 3.9+**（用了 `dict[str, ...]` 等新语法）
2. **克隆仓库**：
   ```bash
   git clone <repo>
   cd mini_agent
   ```
3. **配置 LLM 网关**：复制 `src/mini_agent/config_example.py` 为 `src/mini_agent/config_local.py`，填入你的 `BASE_URL`/`API_KEY`/`MODEL`（`config_local.py` 不进 git，由 `config.py` 自动加载）
4. **选择运行方式**：
   - 开发模式（推荐）：`pip install -e .`
   - 免安装：`$env:PYTHONPATH="src"` (PowerShell) / `PYTHONPATH=src` (bash)

## 如何切版本

```bash
git tag                    # 看所有版本
git checkout v0.1          # 切到第一版
# 读 01-minimal-loop.md
# 跑"使用指导"里的命令
git checkout v0.2          # 看差异，读 02-first-tool.md
# ...依次到最新版
```

## 完整使用手册

[`docs/operation/manual.md`](../operation/manual.md) — 最新版的完整用法、配置、FAQ。
教学文档的"使用指导"只讲**本版**怎么用，想看全量用法去翻 manual。
