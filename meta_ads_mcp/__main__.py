"""Entry point for running the MCP server: `python -m meta_ads_mcp`."""

from meta_ads_mcp.server import mcp


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
