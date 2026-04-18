from mcp.server.fastmcp import FastMCP

from . import albums, duplicates, untagged

_MODULES = (duplicates, albums, untagged)


def register_all(mcp: FastMCP) -> None:
    for module in _MODULES:
        module.register(mcp)
