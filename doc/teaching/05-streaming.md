# 第 5 课：流式输出

> 版本 v0.5 | [上一课](04-permission-gate.md) | [下一课](06-concurrent-tool-calls.md)

## 本课目标

把 `call_llm` 从非流式改成流式：LLM 回复边收边显示，终端逐字出现（打字机效果）。
同时处理流式下 `tool_calls` 的跨 chunk 拼接问题。

## 前置

- 已读 [第 4 课](04-permission-gate.md)，理解权限闸门
- `git checkout v0.5` 切到本版代码

## 新增/改动了什么

```
 src/mini_agent/
 └── agent.py            # 改：call_llm 改流式（stream=True + SSE 解析 + chunk 拼接）
```

> 本版只改 `agent.py` 一个文件。工具、权限、config 都不变。

## 核心概念

### 非流式 vs 流式

**v0.4 非流式**：LLM 生成完整回复后一次性返回 JSON，`call_llm` 解析后返回 message。
终端等到 LLM 全部想完才看到回复——长回复时有明显等待。

**v0.5 流式**：LLM 边生成边发 chunk（Server-Sent Events），每个 chunk 含一小段 content。
`call_llm` 逐 chunk 读取、拼接、实时打印——终端逐字出现，体感更快。

### SSE 协议（Server-Sent Events）

流式响应格式是文本流，每行一个 `data:` 事件：

```
data: {"choices":[{"delta":{"content":"你"}}]}
data: {"choices":[{"delta":{"content":"好"}}]}
data: {"choices":[{"delta":{"content":"！"}}]}
data: [DONE]
```

每个 chunk 的 `delta` 里可能含：
- `content`：一小段文本（边收边打印）
- `tool_calls`：工具调用的片段（跨 chunk 拼接）

`data: [DONE]` 标志流结束。

### call_llm 流式实现（`src/mini_agent/agent.py:12`）

请求变化：
```python
body = json.dumps({
    "model": MODEL,
    "messages": messages,
    "stream": True,              # ← 新增：开启流式
    "tools": registry.schemas(),
}, ensure_ascii=False).encode()

headers = {
    ...
    "Accept": "text/event-stream",  # ← 新增：声明接收 SSE
}
```

解析变化——逐行读取 `resp`，解析每个 `data:` 事件：

```python
content_parts = []
tool_calls_acc = {}

for raw in resp:
    line = raw.decode("utf-8").strip()
    if not line or not line.startswith("data:"):
        continue
    if line == "data: [DONE]":
        break
    chunk = json.loads(line[6:])
    delta = chunk["choices"][0].get("delta", {})

    # content 边收边打印（打字机效果）
    if delta.get("content"):
        content_parts.append(delta["content"])
        print(delta["content"], end="", flush=True)

    # tool_calls 的 arguments 跨 chunk 拼接
    for tc in delta.get("tool_calls", []):
        idx = tc.get("index", 0)
        slot = tool_calls_acc.setdefault(idx, {
            "id": "", "type": "function",
            "function": {"name": "", "arguments": ""},
        })
        if tc.get("id"):
            slot["id"] = tc["id"]
        fn = tc.get("function", {})
        if fn.get("name"):
            slot["function"]["name"] = fn["name"]
        if fn.get("arguments"):
            slot["function"]["arguments"] += fn["arguments"]
```

最终拼接成与非流式格式一致的 message：
```python
message = {"role": "assistant", "content": "".join(content_parts) or None}
if tool_calls_acc:
    message["tool_calls"] = [tool_calls_acc[i] for i in sorted(tool_calls_acc)]
return message
```

### tool_calls 的跨 chunk 拼接

流式下，一个 tool_call 会被拆成多个 chunk 发送：

```
chunk 1: {"tool_calls":[{"index":0, "id":"call_abc", "function":{"name":"calculate"}}]}
chunk 2: {"tool_calls":[{"index":0, "function":{"arguments":"{\"expr"}}]}
chunk 3: {"tool_calls":[{"index":0, "function":{"arguments":"ession\": \"3+5\"}"}}]}
```

`arguments` 是字符串拼接（`+=`），不是 JSON 合并。`index` 标识同一个 tool_call 的不同片段。
用 `tool_calls_acc` 字典按 `index` 聚合，流结束后才得到完整的 tool_calls 列表。

## 为什么这样设计

### 为什么用 http.client 而不是 requests

`your-gateway-host` 网关对 `Accept-Encoding: gzip` 响应异常返回 502。
流式下这个问题更严重——gzip 压缩的 SSE 流可能导致 chunk 边界错乱。
`http.client` + `Accept-Encoding: identity` 保证收到的是未压缩的原始文本流，逐行解析可靠。

### 为什么 content 边收边 print 而不是收完再 print

边收边 print 实现"打字机效果"——用户看到文字逐个出现，体感比等 5 秒后一次性弹出整段好得多。
`print(delta["content"], end="", flush=True)` 的 `flush=True` 强制立即输出，不等缓冲区。

### 为什么 tool_calls 不边收边 print

content 是文本，逐字打印有意义。tool_calls 是结构化数据（工具名 + 参数 JSON），片段打印会乱码。
所以 tool_calls 收完再打印完整决策：`print(f"  决策调用: {name}({arguments})")`。

### 为什么 agent_loop 里 print 标记移到 call_llm 之前

v0.4 的 `agent_loop` 是先调 `call_llm` 再打印 `=== [N] LLM 回复 ===`。
v0.5 改成先打印标记再调 `call_llm`——因为 content 在 `call_llm` 里就流式打印了，
如果标记在后面，终端会先看到回复内容再看到标记，顺序就乱了。

## 使用指导

### 本版可用的命令

```bash
# 单次任务（观察打字机效果）
python -m mini_agent "用一句话介绍你自己"

# 带工具调用
python -m mini_agent "计算 123 * 456"

# 跑 smoke test
$env:PYTHONPATH="src"; python tests/test_tools.py
```

### 本版典型示例

**示例 1：观察打字机效果**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "用一句话介绍你自己"
```
预期：终端逐字出现 LLM 的回复，而不是等几秒后一次性弹出。
注意：回复会打印两遍——第一遍是 `call_llm` 里流式打印，第二遍是 `__main__.py` 里 `print(reply)`。
这是 v0.5 的已知小瑕疵（后续版本会优化 `__main__.py` 不重复打印）。

**示例 2：流式 + 工具调用**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "计算 123 * 456"
```
预期输出：
```
=== [1] LLM 回复 ===
  决策调用: calculate({"expression": "123 * 456"})
[Executor] 执行 Tool: calculate
...
  执行结果: 56088

=== [2] LLM 回复 ===
123 × 456 的计算结果是 56088。
```
注意：第 2 轮的最终回复是流式逐字出现的。

**示例 3：长回复体感对比**
```bash
# v0.4（非流式）：等 3-5 秒后一次性弹出
git checkout v0.4
$env:PYTHONPATH="src"; python -m mini_agent "详细介绍 Python 的历史"

# v0.5（流式）：立刻开始逐字出现
git checkout v0.5
$env:PYTHONPATH="src"; python -m mini_agent "详细介绍 Python 的历史"
```

### 本版独有特性

- **打字机效果**：终端逐字出现 LLM 回复，这是 v0.5 最明显的体感变化。
- **SSE 解析**：`call_llm` 里逐行读取 `data:` 事件，解析 JSON chunk。
- **tool_calls 跨 chunk 拼接**：`arguments` 字符串分片到达，用 `+=` 拼接，`index` 聚合。
- **回复打印两遍**：`call_llm` 流式打印 + `__main__.py` 的 `print(reply)`，已知小瑕疵。

## 动手验证

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_tools.py
   ```
   预期：8 个 PASS（工具测试不受流式影响）。

2. **观察打字机效果**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "用一句话介绍你自己"
   ```
   预期：终端逐字出现回复。

3. **对比 v0.4 vs v0.5**：
   ```bash
   git checkout v0.4
   $env:PYTHONPATH="src"; python -m mini_agent "详细介绍 Python 的历史"
   # 感受：等几秒后一次性弹出

   git checkout v0.5
   $env:PYTHONPATH="src"; python -m mini_agent "详细介绍 Python 的历史"
   # 感受：立刻开始逐字出现
   ```

## 本版完整代码

- [`src/mini_agent/agent.py`](../../src/mini_agent/agent.py) — 流式 `call_llm` + `agent_loop`
