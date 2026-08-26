# mini_agent 操作手册

> 本手册跟随最新版本更新。当前对应版本：**v0.3**（文件读写工具：read_file/write_file）。

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

## 3. 当前能力（v0.3）

v0.3 引入了文件读写工具：

### 3.1 工具

| 工具 | 参数 | 说明 |
|---|---|---|
| `calculate` | `expression: str` | 计算数学表达式（仅数字与 `+-*/()` ） |
| `read_file` | `path: str` | 读取文本文件内容 |
| `write_file` | `path: str, content: str` | 将内容写入文本文件 |

### 3.2 工具调用流程
1. LLM 返回 `tool_calls`（指定工具名 + 参数）
2. `ToolExecutor` 执行对应 handler，异常捕获返回错误信息
3. 结果作为 `role=tool` 消息回灌，进入下一轮
4. LLM 拿着工具结果生成最终回复（无 tool_calls 则结束）

### 3.3 无权限交互
v0.3 所有工具直接执行，不问用户（v0.4 才加权限闸门）。

### 3.4 相对路径约定
工具的相对路径（如 `examples/input.txt`）从**项目根目录** `mini_agent/` 起算：
```bash
# 在 mini_agent/ 目录下运行
python -m mini_agent "读取 examples/input.txt"
```

---

## 4. 测试

### 4.1 运行 smoke test
```bash
# 需 PYTHONPATH=src（未 pip install 时）
$env:PYTHONPATH="src"; python tests/test_tools.py
```
覆盖：registry 注册、calculate 正常/非法输入、重复注册、未知工具。

### 4.2 快速验证 import 链路
```bash
$env:PYTHONPATH="src"
python -c "from mini_agent.tools import registry; print([t.name for t in registry.list_tools()])"
# 期望输出: ['calculate']
```

---

## 5. 常见问题

### Q1：运行报 502 / 连接网关失败
确认 `config.py` 的 `BASE_URL` 和 `API_KEY` 正确，且网络可达 `your-gateway-host`。
> 注意：必须用 `http.client`（代码已如此），不能用 requests/urllib——网关对 `Accept-Encoding: gzip` 响应异常。`call_llm` 已显式设 `Accept-Encoding: identity` 绕过。

### Q2：任务没完成就停了
可能触发 `MAX_ITERATIONS=10` 上限，agent 返回 `"达到最大迭代次数"`。改 `config.py` 调高即可，但注意长对话会累积上下文。

### Q3：中文乱码（Windows 控制台）
`__main__.py` 已对 win32 设 `sys.stdout.reconfigure(encoding="utf-8")`。若仍乱码，PowerShell 执行 `chcp 65001` 切到 UTF-8。
