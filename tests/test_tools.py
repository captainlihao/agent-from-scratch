"""Smoke test for mini_agent v0.2 tools.

验证 Tool/ToolRegistry/ToolExecutor + calculate 工具。
可独立运行：python tests/test_tools.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_agent.tools import registry, executor
from mini_agent.tools.base import Tool, ToolRegistry, ToolExecutor


def test_registry():
    names = [t.name for t in registry.list_tools()]
    assert names == ["calculate"], names
    print("PASS: registry 包含 calculate")


def test_calculate():
    result = executor.execute("calculate", {"expression": "3 + 5 * 2"})
    assert result == "13", result
    print("PASS: calculate 3 + 5 * 2 == 13")


def test_calculate_invalid():
    result = executor.execute("calculate", {"expression": "import os"})
    assert "失败" in result, result
    print("PASS: calculate 拒绝非法字符")


def test_registry_duplicate():
    reg = ToolRegistry()
    reg.register(Tool(
        name="dummy", description="d", parameters={},
        handler=lambda: None,
    ))
    try:
        reg.register(Tool(
            name="dummy", description="d", parameters={},
            handler=lambda: None,
        ))
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("PASS: registry 拒绝重复注册")


def test_executor_unknown():
    try:
        executor.execute("nonexistent", {})
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("PASS: executor 对未知工具抛 ValueError")


if __name__ == "__main__":
    test_registry()
    test_calculate()
    test_calculate_invalid()
    test_registry_duplicate()
    test_executor_unknown()
    print("\n全部 smoke test 通过")
