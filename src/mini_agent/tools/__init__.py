from mini_agent.tools.base import ToolRegistry, ToolExecutor, Tool
from mini_agent.tools.calc import calculate_tool

registry = ToolRegistry()
registry.register(calculate_tool)

executor = ToolExecutor(registry)
