"""带工具的 Agent Loop：调 LLM -> 若要工具则执行 -> 结果回灌 -> 再调，循环到纯文本回复或上限。"""

import http.client
import json
from urllib.parse import urlparse

from mini_agent.tools import registry, executor
from mini_agent.config import BASE_URL, API_KEY, MODEL, MAX_ITERATIONS


def call_llm(messages):
    """非流式调用 LLM，返回 assistant message dict。

    用 http.client + Accept-Encoding: identity 绕过网关 502。
    带 tools 参数（function calling 协议），让 LLM 能决定调哪个工具。
    """
    p = urlparse(BASE_URL)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=120)
    body = json.dumps(
        {
            "model": MODEL,
            "messages": messages,
            "tools": registry.schemas(),
        },
        ensure_ascii=False,
    ).encode()
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept-Encoding": "identity",
    }
    conn.request("POST", f"{p.path.rstrip('/')}/chat/completions", body=body, headers=headers)
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8"))
    conn.close()
    return data["choices"][0]["message"]


def agent_loop(messages):
    """循环：调 LLM -> 有 tool_calls 就执行并回灌 -> 无则结束。

    messages 由调用方维护并跨轮复用，本函数只往里 append。
    """
    for i in range(MAX_ITERATIONS):
        msg = call_llm(messages)
        messages.append(msg)

        print(f"\n=== [{i+1}] LLM 回复 ===")
        # content 可能为 None（LLM 只返回 tool_calls 时）
        if msg.get("content"):
            print(msg["content"])

        # 无 tool_calls = 模型给出最终文本回复，结束
        if not msg.get("tool_calls"):
            return msg.get("content", "")

        # 有 tool_calls：执行，结果作为 role=tool 回灌
        for tc in msg["tool_calls"]:
            name = tc["function"]["name"]
            args = json.loads(tc["function"]["arguments"])
            print(f"  决策调用: {name}({args})")

            result = executor.execute(name, args)
            print(f"  执行结果: {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": str(result),
            })

    return "达到最大迭代次数"
