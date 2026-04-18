from mcp.server.fastmcp import FastMCP

from . import activities, albums, assets, duplicates, health, people, search, shared_links, tags, user

_MODULES = (health, assets, search, albums, people, tags, shared_links, activities, duplicates, user)


def register_all(mcp: FastMCP) -> None:
    for module in _MODULES:
        module.register(mcp)
