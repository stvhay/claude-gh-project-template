"""Structural enforcement tests for tools/ package.

These tests verify that MCP tools follow the register() pattern
and are not added directly to mcp_server.py.
"""
import ast
import importlib
from pathlib import Path


def test_no_mcp_tool_decorator_in_mcp_server():
    """mcp_server.py must not contain @mcp.tool() decorators."""
    server_path = Path("src/ragling/mcp_server.py")
    content = server_path.read_text()
    tree = ast.parse(content)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    func = decorator.func
                    if isinstance(func, ast.Attribute) and func.attr == "tool":
                        raise AssertionError(
                            f"Found @mcp.tool() decorator on {node.name} in mcp_server.py. "
                            f"Tools must be in src/ragling/tools/<name>.py with register(mcp, ctx) pattern."
                        )


def test_all_tool_modules_export_register():
    """Every .py file in tools/ (except __init__.py, context.py, helpers.py) must export register()."""
    tools_dir = Path("src/ragling/tools")
    skip = {"__init__.py", "context.py", "helpers.py"}
    for py_file in sorted(tools_dir.glob("*.py")):
        if py_file.name in skip:
            continue
        module_name = f"ragling.tools.{py_file.stem}"
        mod = importlib.import_module(module_name)
        assert hasattr(mod, "register"), (
            f"{module_name} does not export register(). "
            f"All tool modules must define: def register(mcp: FastMCP, ctx: ToolContext) -> None"
        )


def test_mcp_server_has_no_tool_functions():
    """mcp_server.py should only define create_server(), no other public functions."""
    server_path = Path("src/ragling/mcp_server.py")
    content = server_path.read_text()
    tree = ast.parse(content)
    public_functions = [
        node.name for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    ]
    assert public_functions == ["create_server"], (
        f"mcp_server.py defines public functions {public_functions}. "
        f"Only create_server() should be defined here. Tools go in tools/<name>.py."
    )
