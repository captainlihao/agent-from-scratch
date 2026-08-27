# 第 2 课：第一个工具

> 版本 v0.02 | [上一课](01-minimal-loop.md) | [下一课](03-file-tools.md)

## 本课目标

给 agent 接上第一个工具 `calculate`，让 LLM 能真正"做事"而不只是聊天。
引入 `Tool`/`ToolRegistry`/`ToolExecutor` 三件套和 OpenAI function calling 协议。

## 前置

- 已读 [第 1 课](01-minimal-loop.md)，理解 agent loop 的循环结构
- `git checkout v0.02` 切到本版代码

## 新增/改动了什么

```
 src/mini_agent/
+├── tools/
+│   ├── __init__.py     # 注册中心：创建 registry + executor，注册 calculate
+│   ├── base.py         # Tool / ToolRegistry / ToolExecutor
+│   └── calc.py         # calculate 工具
 ├── agent.py            # 改：call_llm 加 tools 参数；agent_loop 加 tool_calls 执行 + role=tool 回灌
 └── __main__.py         # 改：system prompt 从"你是一个助手"改为"通过调用工具完成任务"
+tests/
+└── test_tools.py        # 新增：工具 smoke test
```

## 核心概念

### 工具三件套：Tool / ToolRegistry / ToolExecutor

**Tool**（`src/mini_agent/tools/base.py:14`）——一个工具的完整定义：

```python
@dataclass
class Tool:
    name: str           # 给 LLM 看的工具名称
    description: str    # 给 LLM 看的工具说明
    parameters: dict    # 给 LLM 看的参数 Schema（JSON Schema）
    handler: Callable   # Runtime 真正执行的 Python 函数
```

一个 Tool 同时携带"给 LLM 的描述"和"给 runtime 的实现"。`to_llm_schema()` 把它转成 OpenAI function calling 需要的格式。

**ToolRegistry**（`base.py:45`）——注册中心，负责注册/查找/列举工具，生成给 LLM 的 schemas 列表。

**ToolExecutor**（`base.py:82`）——执行器，拿到工具名 + 参数，调 handler，捕获异常返回错误信息。v0.02 版无权限闸门（v0.04 才加）。

### calculate 工具（`src/mini_agent/tools/calc.py`）

```python
def calculate(expression: str):
    if not re.fullmatch(r"[\d\s+\-*/().]+", expression):
        raise ValueError("表达式包含非法字符")
    return str(eval(expression))
```

用正则白名单限制只允许数字和数学运算符，防注入。`eval` 在白名单保护下使用。

### function calling 协议

v0.01 的 `call_llm` 只发 `model` + `messages`。v0.02 加了 `tools` 参数：

```python
body = json.dumps({
    "model": MODEL,
    "messages": messages,
    "tools": registry.schemas(),   # ← 新增：把所有工具的 schema 发给 LLM
}, ensure_ascii=False).encode()
```

LLM 收到 `tools` 后，回复里可能带 `tool_calls`：

```python
{
    "role": "assistant",
    "content": None,                # 可能为 null
    "tool_calls": [{
        "id": "call_abc123",
        "type": "function",
        "function": {
            "name": "calculate",
            "arguments": "{\"expression\": \"3+5*2\"}"
        }
    }]
}
```

### agent_loop 的 tool_calls 分支（`src/mini_agent/agent.py:55`）

v0.01 的 loop 只判断"无 tool_calls 就结束"。v0.02 补上了"有 tool_calls"分支：

```python
if not msg.get("tool_calls"):
    return msg.get("content", "")    # 无工具调用 = 最终回复，结束

# 有 tool_calls：执行，结果作为 role=tool 回灌
for tc in msg["tool_calls"]:
    name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    result = executor.execute(name, args)

    messages.append({
        "role": "tool",
        "tool_call_id": tc["id"],      # 必须对应 tool_calls 里的 id
        "content": str(result),
    })
# 循环回到顶部，带着工具结果再调 LLM
```

关键点：`role=tool` 消息必须带 `tool_call_id`，LLM 靠它把结果对应到发起的 tool_call。回灌后进入下一轮循环，LLM 拿着工具结果生成最终回复。

## 为什么这样设计

### 为什么 Tool 同时带"给 LLM 的描述"和"给 runtime 的 handler"

把"LLM 看到的"和"实际执行的"绑在一个对象里，注册时一步到位。对比另一种设计（先注册 schema，再单独绑 handler），这种更不容易漏配。

### 为什么 Executor 捕获异常而不是让 loop 崩

v0.01 的约束是"loop 不兜底"。但工具层不同：工具失败是可预期的（文件不存在、表达式非法），应该把错误信息返回给 LLM，让 LLM 决定下一步（换个参数重试或告诉用户）。所以 `ToolExecutor.execute` 里有 try/except，但这不违反"loop 不兜底"——容错在工具层，不在 loop 层。

### 为什么 tool_calls 串行执行

v0.02 串行执行同一轮的多个 tool_calls。v0.06 才改成 `ThreadPoolExecutor` 并发。先串行是为了让逻辑清晰——看 v0.02 的 loop 能一眼读懂"取 tool_call → 执行 → 回灌"。

## 使用指导

### 本版可用的命令

```bash
# 单次任务
python -m mini_agent "计算 3+5*2"

# 交互模式
python -m mini_agent

# 跑 smoke test
$env:PYTHONPATH="src"; python tests/test_tools.py
```

### 本版典型示例

**示例 1：让 LLM 调 calculate**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "计算 123 * 456"
```
预期输出：
```
=== [1] LLM 回复 ===
  决策调用: calculate({'expression': '123 * 456'})
[Executor] 执行 Tool: calculate
[Executor] 参数: {'expression': '123 * 456'}
  执行结果: 56088

=== [2] LLM 回复 ===
123 × 456 的结果是 56,088。
```
注意两轮循环：第 1 轮 LLM 决策调工具，第 2 轮 LLM 拿着结果给出最终回复。

**示例 2：LLM 自己能算的就不调工具**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "1+1等于几"
```
预期：LLM 可能直接回答"2"而不调 calculate——简单算术它自己能做。这取决于 LLM 的判断。

**示例 3：复杂表达式触发工具**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "计算 (100 + 200) * 3 / 5"
```
预期：LLM 调 `calculate({'expression': '(100 + 200) * 3 / 5'})`，结果 180。

### 本版独有特性

- **观察 role=tool 回灌**：看终端日志，第 1 轮 LLM 返回 `tool_calls`，执行后结果作为 `role=tool` 消息回灌，第 2 轮 LLM 才给出最终文本回复。
- **content 为 null**：LLM 只返回 tool_calls 时，`content` 字段可能是 `null`，agent.py 里用 `if msg.get("content")` 判空跳过打印。
- **无权限交互**：v0.02 所有工具直接执行，不问用户（v0.04 才加权限闸门）。

## 动手验证

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_tools.py
   ```
   预期：5 个 PASS + "全部 smoke test 通过"。

2. **让 agent 算数**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "计算 999 * 999"
   ```
   预期：LLM 调 calculate，结果 998001。

3. **观察两轮循环**：注意终端里 `=== [1]` 和 `=== [2]` 两个标记，理解"第 1 轮调工具、第 2 轮给答案"的流程。

## 本版完整代码

- [`src/mini_agent/tools/base.py`](../../src/mini_agent/tools/base.py) — Tool / ToolRegistry / ToolExecutor
- [`src/mini_agent/tools/calc.py`](../../src/mini_agent/tools/calc.py) — calculate 工具
- [`src/mini_agent/tools/__init__.py`](../../src/mini_agent/tools/__init__.py) — 注册中心
- [`src/mini_agent/agent.py`](../../src/mini_agent/agent.py) — 改造后的 call_llm + agent_loop
- [`tests/test_tools.py`](../../tests/test_tools.py) — 工具 smoke test
