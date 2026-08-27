from mini_agent.tools.base import ToolRegistry, ToolExecutor, Tool
from mini_agent.tools.calc import calculate_tool
from mini_agent.tools.file import (
    read_file_tool,
    write_file_tool,
    edit_file_tool,
    list_dir_tool,
    grep_tool,
)
from mini_agent.tools.shell import run_shell_tool
from mini_agent.permission import PermissionGate

registry = ToolRegistry()
registry.register(calculate_tool)
registry.register(read_file_tool)
registry.register(write_file_tool)
registry.register(edit_file_tool)
registry.register(list_dir_tool)
registry.register(grep_tool)
registry.register(run_shell_tool)

executor = ToolExecutor(registry)
