"""最简 Agent Loop：调 LLM -> 回复 -> 再调，循环到结束或上限。"""

import http.client
import json
from urllib.parse import urlparse

from mini_agent.config import BASE_URL, API_KEY, MODEL, MAX_ITERATIONS


def call_llm(messages):
    """非流式调用 LLM，返回 assistant message dict。

    用 http.client + Accept-Encoding: identity 绕过网关 502。
    """
    p = urlparse(BASE_URL)
    conn = http.client.HTTPConnection(p.hostname, p.port or 80, timeout=120)
    body = json.dumps(
        {"model": MODEL, "messages": messages},
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
    """循环：调 LLM -> 打印回复 -> 无 tool_calls 则结束。

    messages 由调用方维护并跨轮复用，本函数只往里 append。
    """
    for i in range(MAX_ITERATIONS):
        msg = call_llm(messages)
        messages.append(msg)

        print(f"\n=== [{i+1}] LLM 回复 ===")
        print(msg.get("content", ""))

        # 无 tool_calls = 模型给出最终文本回复，结束
        if not msg.get("tool_calls"):
            return msg.get("content", "")

    return "达到最大迭代次数"
