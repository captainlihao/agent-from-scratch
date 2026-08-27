# 第 4 课：权限闸门

> 版本 v0.04 | [上一课](03-file-tools.md) | [下一课](05-streaming.md)

## 本课目标

给 agent 加上权限闸门：有副作用的工具（如 `write_file`）执行前先问用户。
引入 `permission.py` 的 allow/deny/ask 三态权限模型和 `PermissionGate`。

## 前置

- 已读 [第 3 课](03-file-tools.md)，理解 read_file/write_file 工具
- `git checkout v0.04` 切到本版代码

## 新增/改动了什么

```
 src/mini_agent/
+├── permission.py        # 新增：PermissionPolicy + PermissionGate（allow/deny/ask 三态）
 └── tools/
     ├── base.py          # 改：ToolExecutor 加 gate 参数，execute 里先过闸门
     ├── __init__.py      # 改：import PermissionGate（executor 自动创建默认 gate）
     ├── calc.py          # 不变
     └── file.py          # 不变
 tests/
 └── test_tools.py        # 改：write_file 用放行策略绕过 ASK；新增 DENY 测试
```

## 核心概念

### 三态权限模型（`src/mini_agent/permission.py`）

每个工具有三种权限状态：

```python
ALLOW, DENY, ASK = "allow", "deny", "ask"

PERMISSION_RULES = {
    "read_file": ALLOW,    # 无副作用，直接放行
    "calculate": ALLOW,    # 无副作用，直接放行
    "write_file": ASK,     # 有副作用，每次问一下
}
```

- **ALLOW**：直接执行，不问
- **DENY**：直接拒绝，不执行
- **ASK**：每次执行前问用户 `[once/always/reject]`

### PermissionPolicy（`permission.py:27`）

策略对象，负责"查规则"：

```python
class PermissionPolicy:
    def __init__(self, rules: dict | None = None):
        self.rules = rules if rules is not None else PERMISSION_RULES
        self._approved = set()  # 运行时"本轮已批准"的工具名

    def check(self, tool_name, args=None) -> str:
        action = self.rules.get(tool_name, ALLOW)
        if action == ASK:
            if tool_name in self._approved:
                return ALLOW  # 本轮已批准，免再问
            return ASK
        return action
```

关键点：`_approved` 集合实现"always"语义——用户选了 always 后，本轮内同名工具不再问。

### PermissionGate（`permission.py:58`）

闸门对象，封装"检查 + 交互 + 锁"：

```python
class PermissionGate:
    def guard(self, tool_name: str, args: dict) -> str | None:
        action = self.policy.check(tool_name, args)

        if action == DENY:
            return f"权限拒绝: 规则禁止调用 {tool_name}"

        if action == ASK:
            with self._ask_lock:
                choice = input(
                    f"允许执行 {tool_name}({args})? [once/always/reject] "
                ).strip().lower()
                if choice == "always":
                    self.policy.approve(tool_name)
                elif choice != "once":
                    return f"权限拒绝: 用户拒绝执行 {tool_name}"

        return None  # None = 放行，str = 拒绝原因
```

返回约定：`None` 表示放行，`str` 表示拒绝原因（会被回灌给 LLM）。

### ToolExecutor 集成闸门（`src/mini_agent/tools/base.py:93`）

```python
class ToolExecutor:
    def __init__(self, registry: ToolRegistry, gate: PermissionGate | None = None):
        self.registry = registry
        self.gate = gate or PermissionGate()  # 不传则用默认策略

    def execute(self, name: str, arguments: dict):
        tool = self.registry.get(name)

        # ① 权限闸门
        denied = self.gate.guard(name, arguments)
        if denied:
            print(f"[Permission] {denied}")
            return denied  # 拒绝原因回灌给 LLM

        # ② 执行 handler
        try:
            result = tool.handler(**arguments)
        except Exception as e:
            return f"Tool 执行失败: {e}"
        return result
```

Executor 只需调 `gate.guard(name, args)`，不用关心是 ALLOW/DENY/ASK 的细节——闸门内部处理一切。

## 为什么这样设计

### 为什么是三态不是两态

两态（allow/deny）的问题：有副作用的工具（write_file）如果设 allow 太危险，设 deny 又用不了。
ASK 是"动态决策"——规则说"这个工具需要人确认"，但最终执行与否由用户当下决定。
三态覆盖了"总是允许 / 总是禁止 / 看情况"三种现实需求。

### 为什么用 _approved 集合实现 always

用户选了 `always` 后，`policy.approve(tool_name)` 把工具名加入 `_approved` 集合。
下次 `check` 时发现工具在集合里，直接返回 ALLOW，不再问。
这是"运行时"状态——重启后失效，避免永久授权的风险。

### 为什么 guard 里有 _ask_lock

`_ask_lock` 是 `threading.Lock()`。v0.04 还是串行执行，但为 v0.06 的并发 tool_calls 预留：
并发时多个线程可能同时触发 ASK，锁保证交互不会交错（两个权限提示混在一起用户没法看）。

### 为什么拒绝原因回灌给 LLM

用户拒绝后，`guard` 返回 `"权限拒绝: 用户拒绝执行 write_file"`，这个字符串作为工具结果回灌给 LLM。
LLM 拿到后会理解"用户不让写这个文件"，从而换策略（比如告诉用户"你没授权我写文件"）。
**拒绝不是报错，是一种工具结果**——LLM 能据此调整行为。

## 使用指导

### 本版可用的命令

```bash
# 单次任务（可能触发权限交互）
python -m mini_agent "把'hello'写入 examples/test.txt"

# 跑 smoke test（不触发交互，用放行策略绕过）
$env:PYTHONPATH="src"; python tests/test_tools.py
```

### 本版典型示例

**示例 1：write_file 触发权限交互**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "把'测试内容'写入 examples/test.txt"
```
预期输出：
```
=== [1] LLM 回复 ===
  决策调用: write_file({'path': 'examples/test.txt', 'content': '测试内容'})
允许执行 write_file({'path': 'examples/test.txt', 'content': '测试内容'})? [once/always/reject]
```
此时输入：
- `once`：本次允许，下次 write_file 还会问
- `always`：本轮内所有 write_file 都允许，不再问
- `reject` 或其他：拒绝，工具返回拒绝原因给 LLM

**示例 2：read_file 不触发权限**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "读取 examples/input.txt"
```
预期：read_file 是 ALLOW，直接执行，不问。

**示例 3：拒绝后 LLM 的反应**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "把'hello'写入 examples/test.txt"
# 在权限提示时输入 reject
```
预期：LLM 收到"权限拒绝"后，会告知用户"你没有授权我写文件"或换方式完成任务。

### 本版独有特性

- **权限交互提示**：write_file 执行前出现 `[once/always/reject]` 提示，这是 v0.04 最明显的体感变化。
- **always 免再问**：选了 always 后，本轮内再让 agent 写别的文件，不会再次询问。
- **拒绝是工具结果**：拒绝不会让 agent 崩溃，而是作为工具结果回灌，LLM 据此调整策略。

## 动手验证

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_tools.py
   ```
   预期：8 个 PASS（含"write_file 被 DENY 策略拒绝"）。

2. **触发权限交互**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "把'hello'写入 examples/test.txt"
   ```
   在权限提示时输入 `once`，预期文件被写入。

3. **测试 always**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent
   ```
   输入"把'hello'写入 examples/a.txt"，权限提示时输入 `always`。
   再输入"把'world'写入 examples/b.txt"，预期**不再问权限**直接写。

## 本版完整代码

- [`src/mini_agent/permission.py`](../../src/mini_agent/permission.py) — PermissionPolicy + PermissionGate
- [`src/mini_agent/tools/base.py`](../../src/mini_agent/tools/base.py) — ToolExecutor 加 gate 参数
- [`src/mini_agent/tools/__init__.py`](../../src/mini_agent/tools/__init__.py) — import PermissionGate
- [`tests/test_tools.py`](../../tests/test_tools.py) — 含权限测试（放行/DENY）
