import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations


@pytest.fixture
def mcp():
    return FastMCP("test-immich")


def get_fn(mcp_instance: FastMCP, tool_name: str):
    """Return the raw async function for a registered tool."""
    tool = mcp_instance._tool_manager.get_tool(tool_name)
    assert tool is not None, f"Tool '{tool_name}' not registered"
    return tool.fn


def get_annotations(mcp_instance: FastMCP, tool_name: str) -> ToolAnnotations:
    """Return the ToolAnnotations for a registered tool."""
    tool = mcp_instance._tool_manager.get_tool(tool_name)
    assert tool is not None, f"Tool '{tool_name}' not registered"
    return tool.annotations
