"""Smoke test for mini_agent v0.3 tools.

验证 Tool/ToolRegistry/ToolExecutor + calculate/read_file/write_file。
可独立运行：python tests/test_tools.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from mini_agent.tools import registry, executor
from mini_agent.tools.base import Tool, ToolRegistry, ToolExecutor


def test_registry():
    names = [t.name for t in registry.list_tools()]
    assert names == ["calculate", "read_file", "write_file"], names
    print("PASS: registry 包含 calculate/read_file/write_file")


def test_calculate():
    result = executor.execute("calculate", {"expression": "3 + 5 * 2"})
    assert result == "13", result
    print("PASS: calculate 3 + 5 * 2 == 13")


def test_calculate_invalid():
    result = executor.execute("calculate", {"expression": "import os"})
    assert "失败" in result, result
    print("PASS: calculate 拒绝非法字符")


def test_read_file():
    path = os.path.join(os.path.dirname(__file__), "..", "examples", "input.txt")
    result = executor.execute("read_file", {"path": path})
    assert isinstance(result, str) and result.strip(), result
    print("PASS: read_file 读取 examples/input.txt 成功")


def test_write_file():
    with tempfile.TemporaryDirectory() as tmp:
        target = os.path.join(tmp, "out.txt")
        result = executor.execute("write_file", {"path": target, "content": "hello"})
        assert "已写入" in result, result
        with open(target, "r", encoding="utf-8") as f:
            assert f.read() == "hello"
    print("PASS: write_file 写入临时文件成功")


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
    test_read_file()
    test_write_file()
    test_registry_duplicate()
    test_executor_unknown()
    print("\n全部 smoke test 通过")
