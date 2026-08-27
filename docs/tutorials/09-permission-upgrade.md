# 第 9 课：权限系统升级

> 版本 v0.9 | [上一课](08-file-operations.md) | [下一课](10-shell-execution.md)

## 本课目标

把权限从一维 `tool_name -> action` 升级为二维 `(tool_name, pattern) -> action`，支持按文件路径模式（或命令模式）细粒度控制权限。为 v0.10 `run_shell` 的命令模式权限铺路。

## 前置

- 已读上一课文档
- `git checkout v0.9` 切到本版代码（或直接看 `src/mini_agent/permission.py`）

## 新增/改动了什么

```bash
git diff --stat v0.8..v0.9
```

| 文件 | 改动 |
|------|------|
| `src/mini_agent/permission.py` | 重写：Rule 三元组 + fnmatch + findLast + approve(pattern) + _extract_pattern |
| `tests/test_tools.py` | 新增 4 个二维权限测试 |

> `tools/base.py` 不改——`PermissionGate.guard()` 签名不变，内部从 args 提取 pattern。

## 核心概念

### 1. Rule 三元组：从嵌套 dict 到扁平 list

v0.4 的规则是嵌套 dict：`{"write_file": "ask"}`，只能按工具名控制。

v0.9 内部存扁平 `list[dict]`，每条规则是三元组：

```python
[
    {"permission": "read_file", "pattern": "*", "action": "allow"},
    {"permission": "write_file", "pattern": "*", "action": "ask"},
    {"permission": "read_file", "pattern": "*.env", "action": "deny"},
]
```

构造函数 `_from_config()` 兼容两种格式：

```python
# 简单格式（一维兼容，pattern 默认 "*"）
PermissionPolicy({"write_file": "ask"})

# 复杂格式（二维，按 pattern 细控）
PermissionPolicy({"read_file": {"*": "allow", "*.env": "deny"}})
```

### 2. check()：fnmatch + findLast

```python
def check(self, tool_name: str, pattern: str = "*") -> str:
    merged = self._rules + self._approved
    for rule in reversed(merged):
        if fnmatch.fnmatch(tool_name, rule["permission"]) and fnmatch.fnmatch(pattern, rule["pattern"]):
            return rule["action"]
    return ASK  # 未匹配默认 ask
```

**关键设计**：
- `fnmatch.fnmatch()` 做 wildcard 匹配（`*` 匹配任意字符，`?` 匹配单字符）
- `reversed()` 从后往前找，`findLast` 语义——后出现的规则优先级更高
- 未匹配任何规则时默认 `ask`（安全优先）

**为什么用 findLast？** 运行时 `approved` 规则追加在 `self._approved` 末尾，`merged = rules + approved`，`reversed` 先扫 approved，自然覆盖前面的 `ask` 规则。无需显式删除旧规则。

### 3. approve()：存 (tool_name, pattern)

```python
# v0.4：只存工具名
def approve(self, tool_name: str):
    self._approved.add(tool_name)

# v0.9：存 (tool_name, pattern)
def approve(self, tool_name: str, pattern: str = "*"):
    self._approved.append({
        "permission": tool_name, "pattern": pattern, "action": "allow"
    })
```

效果：用户对 `write_file` + `*.txt` 选 `always` 后，后续写 `.txt` 文件免问，但写 `.py` 文件仍会问。

### 4. _extract_pattern()：从 args 提取 pattern

```python
@staticmethod
def _extract_pattern(tool_name: str, args: dict) -> str:
    if tool_name == "run_shell":
        return args.get("command", "*")  # v0.10 接入 BashArity 后改为泛化模式
    if tool_name in ("read_file", "write_file", "edit_file"):
        return args.get("path", "*")
    return "*"
```

`PermissionGate.guard()` 调 `_extract_pattern()` 从工具参数提取 pattern，传给 `check()`。对非 shell 工具，pattern 是文件路径，`fnmatch` 用 `*.env` 等模式匹配文件名。

## 为什么这样设计

### 为什么不沿用一维？

v0.4 的一维权限 `tool_name -> action` 无法区分同一工具的不同操作。`run_shell` 执行 `git status`（安全）和 `rm -rf /`（危险）共享同一个 action——要么全允许要么全问，粒度太粗。二维权限按命令模式控制：`git *` 可以 allow，`rm *` 可以 deny，其他 ask。

### 为什么用 findLast 而非 first？

OpenCode 的 `evaluate()` 用 `findLast`——后出现的规则优先级更高。这让运行时 `approved` 规则（追加在末尾）自然覆盖前面的 `ask` 规则。如果用 first，approved 规则会被前面的 ask 规则挡住，需要显式删除旧规则，复杂度上升。

### 为什么未匹配默认 ask 而非 allow？

安全优先。新工具或未配置的工具默认需要用户确认，避免静默放行危险操作。

### 为什么 _extract_pattern 对 run_shell 只返回完整命令？

v0.9 只升级权限框架，不实现 BashArity 命令泛化。`run_shell` 工具在 v0.10 才落地。v0.9 的 `_extract_pattern()` 对 `run_shell` 返回完整命令字符串作为占位，v0.10 接入 BashArity 后改为泛化模式（如 `git checkout *`），只需改这一个方法。

### 借鉴了 OpenCode 什么？去掉了什么？

借鉴：
- `evaluate()` 的 `findLast` + `Wildcard.match` + 未匹配默认 ask
- `fromConfig()` 支持简单+复杂两种格式
- `approve()` 存 pattern 而非只存工具名

去掉（CLI 同步交互不需要）：
- 事件总线 `Bus.publish`——`input()` 同步阻塞即可
- `pending` 待处理队列——无异步 UI
- 规则持久化到磁盘——保持内存级
- `CorrectedError`（reject 带说明）——CLI 下难以收集说明

## 使用指导

### 本版可用的命令

```bash
# 跑测试
$env:PYTHONPATH="src"; python tests/test_tools.py

# 验证权限系统
$env:PYTHONPATH="src"
python -c "from mini_agent.permission import PermissionPolicy; p = PermissionPolicy({'read_file': {'*': 'allow', '*.env': 'deny'}}); print(p.check('read_file', 'secret.env'))"
# 期望输出: deny
```

### 本版典型示例

**示例 1：按文件名模式控制读权限**

```python
from mini_agent.permission import PermissionPolicy

policy = PermissionPolicy({"read_file": {"*": "allow", "*.env": "deny", "*.env.example": "allow"}})
policy.check("read_file", "config.env")       # → deny
policy.check("read_file", "config.env.example") # → allow
policy.check("read_file", "README.md")         # → allow
```

**示例 2：always 存 pattern，同类免问**

```python
policy = PermissionPolicy({"write_file": "ask"})
policy.approve("write_file", "*.txt")
policy.check("write_file", "test.txt")  # → allow（approved 了 *.txt）
policy.check("write_file", "test.py")   # → ask（未 approved *.py）
```

**示例 3：findLast 优先级**

```python
policy = PermissionPolicy({"write_file": "ask"})
policy.approve("write_file", "*")
policy.check("write_file", "anything")  # → allow（approved 追加在末尾，覆盖 ask）
```

### 本版独有特性

- **二维权限匹配**：`fnmatch` 按 pattern 控制同一工具的不同操作
- **findLast 优先级**：后出现的规则优先级更高，approved 自然覆盖 ask
- **向后兼容**：旧版简单 dict 格式 `{"write_file": "ask"}` 仍然可用，pattern 默认 `"*"`

## 本版完整代码

- `src/mini_agent/permission.py` — 权限系统核心（Rule 三元组 + check + approve + _extract_pattern）
- `tests/test_tools.py` — 19 个 smoke test（含 4 个新增二维权限测试）
