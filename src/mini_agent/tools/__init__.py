from mini_agent.tools.base import ToolRegistry, ToolExecutor, Tool
from mini_agent.tools.calc import calculate_tool
from mini_agent.tools.file import read_file_tool, write_file_tool

registry = ToolRegistry()
registry.register(calculate_tool)
registry.register(read_file_tool)
registry.register(write_file_tool)

executor = ToolExecutor(registry)
