# 第 6 课：并发 tool_calls

> 版本 v0.6 | [上一课](05-streaming.md) | [下一课](07-system-prompt.md)

## 本课目标

把同一轮的多个 tool_calls 从串行执行改成 `ThreadPoolExecutor` 并发执行。
当 LLM 一次发起多个无依赖的工具调用时，并发执行能显著减少等待时间。

## 前置

- 已读 [第 5 课](05-streaming.md)，理解流式 call_llm
- `git checkout v0.6` 切到本版代码

## 新增/改动了什么

```
 src/mini_agent/
 └── agent.py            # 改：agent_loop 里 tool_calls 执行从串行 for 循环改为 ThreadPoolExecutor 并发
```

> 本版只改 `agent.py` 一个文件，且只改 agent_loop 里的 tool_calls 执行部分。

## 核心概念

### 串行 vs 并发

**v0.5 串行**：同一轮的 N 个 tool_calls 用 `for` 循环逐个执行，总耗时 = Σ(每个工具耗时)。

```python
for tc in msg["tool_calls"]:
    result = executor.execute(name, args)   # 第 2 个等第 1 个跑完才开始
```

**v0.6 并发**：用 `ThreadPoolExecutor` 把 N 个 tool_calls 丢进线程池同时执行，总耗时 ≈ max(每个工具耗时)。

```python
with ThreadPoolExecutor(max_workers=len(tool_calls)) as pool:
    results = list(pool.map(_run, tool_calls))
```

### LLM 何时发多个 tool_calls

LLM 在一轮回复里可以返回多个 `tool_calls`，通常是无依赖的独立调用。例如：

```
用户："同时读取 a.txt 和 b.txt"

LLM 回复（一轮 2 个 tool_calls）:
  tool_calls[0]: read_file({"path": "a.txt"})
  tool_calls[1]: read_file({"path": "b.txt"})
```

这两个 read_file 互不依赖——a.txt 的读取不需要等 b.txt 的结果。串行执行浪费时间，并发执行同时跑完。

### ThreadPoolExecutor 实现（`src/mini_agent/agent.py:95`）

```python
tool_calls = msg["tool_calls"]

def _run(tc):
    name = tc["function"]["name"]
    args = json.loads(tc["function"]["arguments"])
    result = executor.execute(name, args)
    print(f"  执行 {name} -> {result}")
    return tc["id"], str(result)

with ThreadPoolExecutor(max_workers=len(tool_calls)) as pool:
    results = list(pool.map(_run, tool_calls))

for tool_call_id, content in results:
    messages.append({
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    })
```

关键点：
1. **`max_workers=len(tool_calls)`**：线程数 = 本轮 tool_calls 数量，不多不少。
2. **`pool.map`**：按 tool_calls 的原始顺序提交，结果也按原始顺序返回——`results[0]` 对应 `tool_calls[0]`。
3. **`with` 语句**：`ThreadPoolExecutor` 的上下文管理器会在退出时自动 `join()`——等所有线程跑完才继续。
4. **回灌顺序**：`pool.map` 保证结果顺序与输入顺序一致，`role=tool` 消息按原序 append。

## 为什么这样设计

### 为什么用线程而不是协程

`read_file`/`write_file` 是 IO 密集型（磁盘读写），`ThreadPoolExecutor` 能在 IO 等待时切换到其他线程。
协程（asyncio）也能做，但需要把整个调用链改成 async——从 `call_llm` 到 `executor.execute` 全部 async 化，改动太大。
线程池是"最小改动 + 足够好的并发"的选择。

### 为什么 max_workers = len(tool_calls)

每轮的 tool_calls 数量通常很少（2-5 个），直接开对应数量的线程。
不需要复用线程池（每轮新建一个），因为 agent loop 本身是串行的——一轮跑完才进下一轮。

### 为什么 pool.map 而不是 submit + as_completed

`pool.map` 保证**结果顺序与输入顺序一致**。`as_completed` 是谁先完成谁先返回——顺序乱。
tool_calls 的回灌需要按原序（LLM 发的 tool_calls[0] 对应的 tool 消息要在前面），用 map 更安全。

### 为什么权限闸门的 _ask_lock 在这里起作用

v0.4 的 `PermissionGate` 里有 `self._ask_lock = threading.Lock()`。
并发执行时，如果两个 write_file 同时触发 ASK，没有锁会导致两个权限提示交错（终端乱码）。
锁保证同一时刻只有一个 ASK 交互在终端进行——v0.4 埋的伏笔在 v0.6 生效。

## 使用指导

### 本版可用的命令

```bash
# 让 LLM 一次调多个工具（观察并发）
python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"

# 跑 smoke test
$env:PYTHONPATH="src"; python tests/test_tools.py
```

### 本版典型示例

**示例 1：并发读取两个文件**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt，告诉我两个文件的内容"
```
预期输出：
```
=== [1] LLM 回复 ===
  决策调用: read_file({"path": "examples/input.txt"})
  决策调用: read_file({"path": "examples/input2.txt"})
[Executor] 执行 Tool: read_file
[Executor] 参数: {'path': 'examples/input.txt'}
[Executor] 执行 Tool: read_file
[Executor] 参数: {'path': 'examples/input2.txt'}
  执行 read_file -> 3 + 5 * 2
  执行 read_file -> 3 + 5 * 3
```
注意：两个 `[Executor] 执行 Tool: read_file` 几乎同时出现——并发执行的证据。
对比 v0.5 串行版，第一个 read_file 跑完打印结果后，第二个才开始。

**示例 2：并发计算 + 读取**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "计算 100*200，同时读取 examples/input.txt"
```
预期：LLM 一次发 `calculate` + `read_file` 两个 tool_calls，线程池并发执行。

**示例 3：对比串行 vs 并发**
```bash
# v0.5（串行）：两个 read_file 依次执行
git checkout v0.5
$env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"

# v0.6（并发）：两个 read_file 同时执行
git checkout v0.6
$env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"
```

### 本版独有特性

- **并发执行日志**：终端里多个工具的 `[Executor]` 日志交错出现，而非一个跑完再出下一个。
- **结果按原序回灌**：虽然并发执行，但 `pool.map` 保证 results 顺序与 tool_calls 原序一致。
- **权限锁生效**：如果并发触发多个 write_file 的 ASK，锁保证交互不交错。

## 动手验证

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_tools.py
   ```
   预期：8 个 PASS。

2. **并发读取两个文件**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"
   ```
   预期：两个 read_file 的 Executor 日志几乎同时出现，结果一起回灌。

3. **对比 v0.5 vs v0.6**：
   ```bash
   git checkout v0.5
   $env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"
   # 串行：第一个 read_file 结果打印后，第二个才开始

   git checkout v0.6
   $env:PYTHONPATH="src"; python -m mini_agent "同时读取 examples/input.txt 和 examples/input2.txt"
   # 并发：两个 read_file 的 Executor 日志几乎同时出现
   ```

## 本版完整代码

- [`src/mini_agent/agent.py`](../../src/mini_agent/agent.py) — agent_loop 里 tool_calls 并发执行
