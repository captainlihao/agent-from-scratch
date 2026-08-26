"""Smoke test for mini_agent v0.1.

验证 import 链路和函数签名，不实际调用 LLM（避免依赖网络）。
可独立运行：python tests/test_loop.py
（零第三方依赖，仅标准库）
"""

import os
import sys

# 让 tests/ 目录下也能 import 到 src 布局的包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_agent.agent import call_llm, agent_loop
from mini_agent.config import BASE_URL, API_KEY, MODEL, MAX_ITERATIONS


def test_import():
    assert callable(call_llm), "call_llm 应可调用"
    assert callable(agent_loop), "agent_loop 应可调用"
    print("PASS: agent 模块 import 成功，call_llm/agent_loop 可调用")


def test_config():
    assert BASE_URL, "BASE_URL 不能为空"
    assert API_KEY, "API_KEY 不能为空"
    assert MODEL, "MODEL 不能为空"
    assert isinstance(MAX_ITERATIONS, int) and MAX_ITERATIONS > 0
    print(f"PASS: config 加载成功 (MODEL={MODEL}, MAX_ITERATIONS={MAX_ITERATIONS})")


def test_agent_loop_signature():
    import inspect
    sig = inspect.signature(agent_loop)
    params = list(sig.parameters)
    assert params == ["messages"], f"agent_loop 应只接受 messages 参数，实际: {params}"
    print("PASS: agent_loop(messages) 签名正确")


if __name__ == "__main__":
    test_import()
    test_config()
    test_agent_loop_signature()
    print("\n全部 smoke test 通过")
