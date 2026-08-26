# 第 1 课：最简 agent loop

> 版本 v0.1 | [下一课](02-first-tool.md)

## 本课目标

从零搭一个能跑的 agent loop：调 LLM → 拿回复 → 再调，循环到 LLM 不再要求工具就结束。
这一版**没有任何工具**，纯对话循环，先把"什么是 agent loop"讲透。

## 前置

- Python 3.9+
- 已按 [教学路径 README](README.md) 完成环境准备（克隆仓库、填 config.py、装好包）
- `git checkout v0.1` 切到本版代码

## 新增了什么

本版是起点，没有"上一版"。全部文件如下：

```
src/mini_agent/
├── __init__.py         # 包入口（空文件）
├── __main__.py         # CLI 入口：python -m mini_agent
├── agent.py            # agent loop：call_llm + agent_loop
└── config.py           # BASE_URL/API_KEY/MODEL/MAX_ITERATIONS（硬编码）
tests/
└── test_loop.py        # import 链路 smoke test
```

## 核心概念

### 什么是 agent loop

agent 的本质是一个**循环**：

1. 把对话历史（`messages` 列表）发给 LLM
2. LLM 返回一条回复，append 到 `messages`
3. 判断回复里有没有 `tool_calls`
   - 没有 → LLM 给出最终答案，循环结束
   - 有 → 执行工具，把结果 append 回 `messages`，回到第 1 步

v0.1 没有工具，所以第 3 步只会走"没有 tool_calls"分支——LLM 回复一次就结束。但 loop 的骨架已经在了，后续版本只需在"有 tool_calls"分支上接工具。

### messages 列表

整个对话状态就是一个 list of dict：

```python
messages = [
    {"role": "system", "content": "你是一个助手。"},
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "你好！有什么可以帮你？"},
]
```

每轮调用 LLM 时，把**整个 messages** 发过去（LLM 无状态，靠这个列表维持上下文）。LLM 返回的新消息 append 进去，下一轮再发。这就是"对话循环"的全部状态管理。

### call_llm：用 http.client 调 LLM

`src/mini_agent/agent.py:12` 的 `call_llm` 干的事：

```python
def call_llm(messages):
    p = urlparse(BASE_URL)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=120)
    body = json.dumps(
        {"model": MODEL, "messages": messages},
        ensure_ascii=False,
    ).encode()
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept-Encoding": "identity",   # ← 关键，见下文"为什么这样设计"
    }
    conn.request("POST", f"{p.path.rstrip('/')}/chat/completions", body=body, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return data["choices"][0]["message"]
```

用 OpenAI chat completions 协议：POST 到 `{BASE_URL}/chat/completions`，body 里带 `model` 和 `messages`，header 带 `Authorization: Bearer <API_KEY>`。返回的 JSON 里 `data["choices"][0]["message"]` 就是 LLM 的回复消息，直接 append 回 messages 即可。

### agent_loop：循环主体

`src/mini_agent/agent.py:34` 的 `agent_loop`：

```python
def agent_loop(messages):
    for i in range(MAX_ITERATIONS):
        msg = call_llm(messages)
        messages.append(msg)

        print(f"\n=== [{i+1}] LLM 回复 ===")
        print(msg.get("content", ""))

        if not msg.get("tool_calls"):
            return msg.get("content", "")

    return "达到最大迭代次数"
```

三个要点：
1. **messages 由调用方传入并跨轮复用**：`agent_loop` 只往里 append，不负责创建。这样调用方（`__main__.py`）能在多次调用间维持对话。
2. **结束条件**：`if not msg.get("tool_calls")`。v0.1 的 LLM 永远不会返回 tool_calls（因为没传 `tools` 参数），所以第一轮就结束。但这个判断为后续版本预留了分支。
3. **迭代上限**：`MAX_ITERATIONS = 10`。超限直接返回 `"达到最大迭代次数"`，不报错——长任务可能静默截断，后续版本会处理。

### __main__.py：CLI 入口

`src/mini_agent/__main__.py` 支持两种模式：

- **单次任务**：`python -m mini_agent "你的任务"` — 把命令行参数当 user 消息，调一次 loop
- **交互模式**：`python -m mini_agent` — 进入 `你: ` 提示符，每输一行调一次 loop，`exit`/`quit` 退出

两种模式共用同一个 `messages` 列表，所以交互模式下跨轮有上下文。

## 为什么这样设计

### 为什么用 http.client 而不是 requests

`your-gateway-host` 网关对 `Accept-Encoding: gzip` 的响应异常，会返回 502。
`requests` 默认发 `Accept-Encoding: gzip, deflate`，且不易关掉。
`http.client` 是标准库，可以精确控制 header——显式设 `Accept-Encoding: identity` 绕过。

**这是踩坑后的硬约束，换 HTTP 客户端会重新踩坑。** 后续所有版本都遵守。

### 为什么不用 try/except 兜底

`agent_loop` 里没有 try/except。如果 `call_llm` 抛异常（网络断、API key 错、JSON 解析失败），整个 loop 直接崩。

这是有意的：**保持核心路径可读**。第一课的 loop 应该一眼能看懂"调 LLM → 判断 → 结束"。容错是工具层、执行器层的事（v0.2+ 的 `ToolExecutor` 会捕获 handler 异常），loop 本身不该兜底。

### 为什么 config 硬编码

`BASE_URL`/`API_KEY`/`MODEL` 直接写在 `config.py` 里，不读环境变量。教学仓库追求"改一处即生效，重启就跑通"，环境变量会增加配置步骤。后续版本若需多环境部署再改。

## 使用指导

### 本版可用的命令

```bash
# 单次任务模式
python -m mini_agent "你好"

# 交互模式
python -m mini_agent

# 跑 smoke test（验证 import 链路）
$env:PYTHONPATH="src"; python tests/test_loop.py
```

> 未 `pip install -e .` 时需先设 `PYTHONPATH=src`（Windows PowerShell 用 `$env:PYTHONPATH="src"`）。

### 本版典型示例

**示例 1：单次任务**
```bash
$env:PYTHONPATH="src"; python -m mini_agent "用一句话介绍你自己"
```
预期输出：
```
=== [1] LLM 回复 ===
我是一个 AI 助手，可以帮你回答问题、提供建议。
我是一个 AI 助手，可以帮你回答问题、提供建议。
```
（第二行是 `__main__.py` 里 `print(reply)` 打的，和上面重复——v0.1 的小瑕疵，后续会优化）

**示例 2：交互模式**
```bash
$env:PYTHONPATH="src"; python -m mini_agent
```
进入后：
```
你: 我叫小明
=== [1] LLM 回复 ===
你好，小明！有什么可以帮你？
你: 我刚才说我叫什么？
=== [1] LLM 回复 ===
你刚才说你叫小明。
你: exit
```
注意第二轮 LLM 能记住"小明"——因为 `messages` 列表跨轮复用，上下文保留了。

### 本版独有特性

- **无工具**：v0.1 的 LLM 只能纯对话回复，不能调任何工具。问它"读取文件"它会告诉你它做不到，或者瞎编一个答案。
- **非流式**：LLM 回复是整段返回的，终端一次性打印，没有打字机效果（v0.5 才加流式）。
- **无权限交互**：因为没工具，没有任何"是否允许执行"的提示。

## 动手验证

跑完下面三步确认你理解了 v0.1：

1. **跑 smoke test**：
   ```bash
   $env:PYTHONPATH="src"; python tests/test_loop.py
   ```
   预期：打印 `PASS: ...` 四行 + `全部 smoke test 通过`。

2. **单次任务**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent "1+1等于几"
   ```
   预期：LLM 回答"2"（它自己算的，不是调工具——v0.1 没工具）。

3. **交互模式测上下文**：
   ```bash
   $env:PYTHONPATH="src"; python -m mini_agent
   ```
   先输 `我叫张三`，再输 `我叫什么？`，预期 LLM 能答出"张三"。

## 本版完整代码

- [`src/mini_agent/agent.py`](../../src/mini_agent/agent.py) — `call_llm` + `agent_loop`
- [`src/mini_agent/__main__.py`](../../src/mini_agent/__main__.py) — CLI 入口
- [`src/mini_agent/config.py`](../../src/mini_agent/config.py) — 配置
- [`tests/test_loop.py`](../../tests/test_loop.py) — smoke test
