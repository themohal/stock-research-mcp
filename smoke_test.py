"""Quick in-process smoke test: lists tools and calls one live tool.

Run: python smoke_test.py
Uses FastMCP's in-memory client (no network / no running server needed).
"""

import asyncio

from fastmcp import Client

from server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("Tools advertised:", [t.name for t in tools])
        assert len(tools) == 6, f"expected 6 tools, got {len(tools)}"

        result = await client.call_tool("get_quote", {"ticker": "AAPL"})
        print("get_quote('AAPL') ->", result.data)

    print("SMOKE_OK")


if __name__ == "__main__":
    asyncio.run(main())
