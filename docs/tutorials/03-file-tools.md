# 第 3 课：文件读写工具

> 版本 v0.3 | [上一课](02-first-tool.md) | [下一课](04-permission-gate.md)

## 本课目标

给 agent 加上 `read_file`/`write_file` 工具，让它能真正读写文件。
这是 agent 从"能算数"到"能干活"的关键一步——不改文件没法做编程任务。

## 前置

- 已读 [第 2 课](02-first-tool.md)，理解 Tool 三件套和 function calling 协议
- `git checkout v0.3` 切到本版代码

## 新增/改动了什么

```
 src/mini_agent/tools/
+├── file.py             # 新增：read_file / write_file 工具
 ├── __init__.py         # 改：注册 read_file / write_file
 ├── base.py             # 不变
 └── calc.py             # 不变
+examples/
+├── input.txt            # 示例文件（内容：3 + 5 * 2）
+└── input2.txt           # 示例文件（内容：3 + 5 * 3）
 tests/
 └── test_tools.py       # 改：加 read_file / write_file 测试
```

## 核心概念

### read_file / write_file（`src/mini_agent/tools/file.py`）

```python
def read_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path: str, content: str):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"已写入文件: {path}"
```

实现极简：`open` + `read`/`write`。关键在 Tool 定义里的 schema：

```python
read_file_tool = Tool(
    name="read_file",
    description="读取一个文本文件的内容",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "要读取的文件路径"}
        },
        "required": ["path"],
    },
    handler=read_file,
)
```

LLM 靠 `description` 和 `parameters` 理解怎么用这个工具。schema 越清晰，LLM 调用越准确。

### 注册新工具（`src/mini_agent/tools/__init__.py`）

```python
registry = ToolRegistry()
registry.register(calculate_tool)
registry.register(read_file_tool)    # ← 新增
registry.register(write_file_tool)   # ← 新增
```

加工具只需：写 handler → 包成 Tool → 注册。**不动 agent.py，不动 loop 逻辑**。这是 v0.2 三件套分离关注点的好处。

### 多步工具串联

v0.3 最有意思的现象是 LLM 会**自动串联多个工具**。让它"读取 examples/input.txt 并计算"：

```
=== [1] LLM 回复 ===
  决策调用: read_file({'path': 'examples/input.txt'})
  执行结果: 3 + 5 * 2

=== [2] LLM 回复 ===
  决策调用: calculate({'expression': '3 + 5 * 2'})
  执行结果: 13

=== [3] LLM 回复 ===
文件内容为 3 + 5 * 2，计算结果为 13。
```

3 轮循环：第 1 轮读文件，第 2 轮算结果，第 3 轮给最终答案。LLM 自己决定先读后算，agent loop 只负责执行 + 回灌。

## 为什么这样设计

### 为什么 write_file 直接执行不问人

v0.3 的 `write_file` 是**无权限**的——LLM 说写就写。这有风险（可能覆盖重要文件），但 v0.3 故意不加权限，原因有二：
1. 先让"能写文件"这个能力跑通，权限是独立概念，v0.4 专门讲。
2. 教学顺序：能力 → 安全。先有能力再加约束，比一开始就加约束更易理解。

v0.4 会引入 `permission.py`，把 `write_file` 改成 ASK（每次问用户）。

### 为什么用 `"w"` 模式而非 `"a"`

`"w"` 是覆盖写。教学场景下覆盖写更直观——每次 write_file 的结果就是文件最终内容。追加写 `"a"` 的语义更复杂（多次调用会累积），不适合第一版。

### 为什么工具签名是单参数/双参数字符串

`read_file(path: str)` 单参数，`write_file(path: str, content: str)` 双参数。
LLM 的 function calling 对字符串参数最可靠——复杂对象（嵌套 dict/list）LLM 容易生成错。
保持参数类型简单（全字符串），是和 LLM 配合的实用策略。

## 使用指导

### 本版可用的命令

```bash
# 单次任务
python -m mini_agent "读取 examples/input.txt 并计算"

# 交互模式
python -m mini_agent

# 跑 smoke test
$env:PYTHONPATH="src"; python tests/test_tools.py
```

### 本版典型示例

**示例 1：读文件 + 计算（多步串联）**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "读取 examples/input.txt 的内容并计算"
```
预期：3 轮循环，read_file → calculate → 最终回复"13"。

**示例 2：写文件**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "把'Hello World'写入 examples/output.txt"
```
预期：LLM 调 `write_file({'path': 'examples/output.txt', 'content': 'Hello World'})`，回复"已写入"。

**示例 3：读后写（复制文件）**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "读取 examples/input.txt，把内容写入 examples/copy.txt"
```
预期：read_file 拿到内容，write_file 写入 copy.txt。

### 本版独有特性

- **多步工具串联**：LLM 能在一轮对话里串联多个工具（读 → 算 → 答），每步结果回灌后 LLM 自行决定下一步。
- **副作用工具**：write_file 会改文件系统。v0.3 无权限保护，LLM 说写就写——观察这个"危险"行为，理解 v0.4 为什么需要权限闸门。
- **相对路径约定**：工具的相对路径从项目根目录 `mini_agent/` 起算。必须在 `mini_agent/` 目录下运行。

## 动手验证

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_tools.py
   ```
   预期：7 个 PASS + "全部 smoke test 通过"。

2. **读文件 + 计算**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "读取 examples/input.txt 并计算"
   ```
   预期：3 轮循环，最终结果 13。

3. **写文件验证**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "把'测试内容'写入 examples/test.txt"
   ```
   跑完后检查 `examples/test.txt` 是否被创建、内容是否正确。

## 本版完整代码

- [`src/mini_agent/tools/file.py`](../../src/mini_agent/tools/file.py) — read_file / write_file
- [`src/mini_agent/tools/__init__.py`](../../src/mini_agent/tools/__init__.py) — 注册三个工具
- [`tests/test_tools.py`](../../tests/test_tools.py) — 工具 smoke test（含 read_file/write_file）
