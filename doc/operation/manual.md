# mini_agent 操作手册

> 本手册跟随最新版本更新。当前对应版本：**v0.1**（最简 agent loop，无工具）。

## 1. 环境准备

### 1.1 依赖
- Python 3.9+（用了 `dict[str, ...]` 等新语法）
- 零第三方依赖，仅 Python 标准库

### 1.2 安装方式

**方式一：开发模式安装（推荐）**
```bash
cd mini_agent
pip install -e .
```
安装后可从任意目录运行 `python -m mini_agent`。

**方式二：免安装，用 PYTHONPATH**
```bash
# Windows PowerShell
$env:PYTHONPATH="src"
python -m mini_agent
```
```bash
# Linux/macOS
PYTHONPATH=src python -m mini_agent
```

### 1.3 配置
配置硬编码在 `src/mini_agent/config.py`，修改后重启生效：

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `BASE_URL` | `http://your-gateway-host/v3/openai/model` | LLM 网关地址 |
| `API_KEY` | `sk-...` | 网关密钥 |
| `MODEL` | `EB-GLM-5.2` | 模型名 |
| `MAX_ITERATIONS` | `10` | agent loop 最大轮数 |

> 当前不从环境变量读，改配置直接编辑 `config.py`。

---

## 2. 运行

### 2.1 单次任务模式
```bash
python -m mini_agent "你好"
```
任务完成后进入交互模式，可继续追问。

### 2.2 交互模式
```bash
python -m mini_agent
```
启动后进入 `你: ` 提示符，输入任务回车提交。输入 `exit` 或 `quit` 退出，或按 Ctrl+C/Ctrl+D。

---

## 3. 当前能力（v0.1）

v0.1 是最简版本，**无任何工具**：
- LLM 只能纯对话回复
- 不能读写文件、不能执行命令、不能计算
- 每次调用 LLM 后，若回复不含 `tool_calls` 即结束（v0.1 永远走这个分支）

---

## 4. 测试

### 4.1 运行 smoke test
```bash
# 需 PYTHONPATH=src（未 pip install 时）
$env:PYTHONPATH="src"; python tests/test_loop.py
```
覆盖：import 链路、call_llm 签名、agent_loop 签名。

### 4.2 快速验证 import 链路
```bash
$env:PYTHONPATH="src"
python -c "from mini_agent.agent import agent_loop, call_llm; print('import ok')"
# 期望输出: import ok
```

---

## 5. 常见问题

### Q1：运行报 502 / 连接网关失败
确认 `config.py` 的 `BASE_URL` 和 `API_KEY` 正确，且网络可达 `your-gateway-host`。
> 注意：必须用 `http.client`（代码已如此），不能用 requests/urllib——网关对 `Accept-Encoding: gzip` 响应异常。`call_llm` 已显式设 `Accept-Encoding: identity` 绕过。

### Q2：任务没完成就停了
v0.1 无工具，LLM 回复一次就结束。如果 LLM 回复里说"我去读取文件"但实际没读——这是 LLM 在瞎编，v0.1 确实做不到。v0.2+ 加工具后才有真实能力。

### Q3：中文乱码（Windows 控制台）
`__main__.py` 已对 win32 设 `sys.stdout.reconfigure(encoding="utf-8")`。若仍乱码，PowerShell 执行 `chcp 65001` 切到 UTF-8。
