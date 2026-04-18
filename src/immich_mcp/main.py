import argparse

from mcp.server.fastmcp import FastMCP

from .client import managed_client
from .prompts import register_all as register_prompts
from .tools import register_all as register_tools


def main() -> None:
    parser = argparse.ArgumentParser(description="Immich MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport mode (default: stdio)",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host for HTTP transports")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP transports")
    args = parser.parse_args()

    mcp = FastMCP(
        "immich-mcp",
        lifespan=managed_client,
        host=args.host,
        port=args.port,
        instructions=(
            "MCP server for Immich photo management. "
            "Provides tools for browsing, searching, organizing, and managing photos and videos. "
            "Includes duplicate detection and safe deletion workflows. "
            "Always use dry_run=true before executing destructive operations."
        ),
    )

    register_tools(mcp)
    register_prompts(mcp)

    mcp.run(transport=args.transport)


if __name__ == "__main__":
    main()
