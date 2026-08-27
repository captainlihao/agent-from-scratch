# mini_agent 操作手册

> 本手册跟随最新版本更新。当前对应版本：**v0.8**（文件操作补全）。

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
配置分两层：`config.py`（占位模板，进 git）+ `config_local.py`（真实配置，不进 git）。

首次使用：复制 `src/mini_agent/config_example.py` 为 `src/mini_agent/config_local.py`，填入真实值。`config.py` 会自动 `import *` 加载 `config_local.py` 覆盖占位值。

| 配置项 | 占位值 | 说明 |
|---|---|---|
| `BASE_URL` | `http://your-gateway-host/v3/openai/model` | LLM 网关地址 |
| `API_KEY` | `sk-YOUR_API_KEY_HERE` | 网关密钥 |
| `MODEL` | `EB-GLM-5.2` | 模型名 |
| `MAX_ITERATIONS` | `10` | agent loop 最大轮数 |

> 真实配置写进 `config_local.py`（不进 git）；无 `config_local.py` 时回退到 `config.py` 占位值。

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

## 3. 当前能力（v0.8）

v0.8 补全了文件操作能力，agent 具备"浏览→定位→读取→编辑"的完整文件操作链路。v0.7 的系统提示词工程化仍然生效。

### 3.1 System Prompt

启动时由 `prompt.py` 的 `build_system_prompt()` 组装 `messages[0]`，分三层：

| 层 | 函数/常量 | 内容 |
|---|---|---|
| 身份 | `header(agent_name)` | 告诉模型是哪个 agent（当前只有 build，为多 agent 预留） |
| 行为规范 | `_CORE_RULES` | tone、专业客观性、工具用法、安全约束 |
| 环境信息 | `environment()` | 工作目录、git 状态、平台、日期（动态生成） |

查看当前 system prompt：
```bash
$env:PYTHONPATH="src"; python -c "from mini_agent.prompt import build_system_prompt; print(build_system_prompt())"
```

### 3.2 工具

| 工具 | 参数 | 权限 | 说明 |
|---|---|---|---|
| `calculate` | `expression: str` | allow | 计算数学表达式（仅数字与 `+-*/()` ） |
| `read_file` | `path: str, offset?: int, limit?: int` | allow | 读取文本文件，支持分段读取，输出带行号前缀 |
| `write_file` | `path: str, content: str` | **ASK** | 写文件（完整覆盖），每次执行前问用户 |
| `edit_file` | `path: str, old_string: str, new_string: str, replace_all?: bool` | **ASK** | 精确字符串替换，多匹配时需 replace_all 或更长上下文 |
| `list_dir` | `path?: str` | allow | 列出目录内容，目录加 `/` 后缀，上限 200 条 |
| `grep` | `pattern: str, path?: str, include?: str` | allow | 正则搜索文件内容，返回 `file:line: content`，上限 100 条 |

### 3.3 权限交互
`write_file`/`edit_file` 执行前会提示：
```
允许执行 write_file({...})? [once/always/reject]
```
- `once`：本次允许，下次再问
- `always`：本轮运行内总是允许，不再问
- 其他输入：拒绝执行，工具返回拒绝原因给 LLM

> `edit_file` 同样走 ASK 权限，交互方式相同。

### 3.4 工具调用流程
1. LLM 返回 `tool_calls`（一轮可含多个，代码用线程池并发执行）
2. `ToolExecutor` 先过权限闸门（`PermissionGate.guard`）
3. 通过则调 handler，失败则捕获异常返回错误信息给 LLM
4. 结果作为 `role=tool` 消息回灌，进入下一轮

### 3.5 相对路径约定
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
$env:PYTHONPATH="src"; python tests/test_prompt.py   # system prompt
$env:PYTHONPATH="src"; python tests/test_loop.py      # import 链路
$env:PYTHONPATH="src"; python tests/test_tools.py     # 工具 + 权限
```
覆盖：system prompt 分层组装、import 链路、registry 注册、calculate 正常/非法输入、read_file 分段读取、读写文件、edit_file 精确替换/多匹配安全检查、list_dir、grep、权限闸门。

### 4.2 快速验证 import 链路
```bash
$env:PYTHONPATH="src"
python -c "from mini_agent.tools import registry; print([t.name for t in registry.list_tools()])"
# 期望输出: ['calculate', 'read_file', 'write_file', 'edit_file', 'list_dir', 'grep']
```

---

## 5. 常见问题

### Q1：运行报 502 / 连接网关失败
确认 `config_local.py` 的 `BASE_URL` 和 `API_KEY` 正确，且网络可达 `your-gateway-host`。
> 注意：必须用 `http.client`（代码已如此），不能用 requests/urllib——网关对 `Accept-Encoding: gzip` 响应异常。`call_llm` 已显式设 `Accept-Encoding: identity` 绕过。

### Q2：任务没完成就停了
可能触发 `MAX_ITERATIONS=10` 上限，agent 返回 `"达到最大迭代次数"`。改 `config_local.py` 调高即可，但注意长对话会累积上下文。

### Q3：工具失败直接报错退出
这是有意为之——agent loop 不加 try/except 兜底，保持核心逻辑清晰。工具层（`ToolExecutor.execute`）会捕获 handler 异常并返回错误信息给 LLM，但 loop 本身的异常会向上抛。

### Q4：write_file 被拒绝
检查权限交互的输入。选 `reject` 或输错字符会拒绝。重新运行即可。

### Q3：中文乱码（Windows 控制台）
`__main__.py` 已对 win32 设 `sys.stdout.reconfigure(encoding="utf-8")`。若仍乱码，PowerShell 执行 `chcp 65001` 切到 UTF-8。
