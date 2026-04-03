import asyncio
import json
from typing import Any

from fastmcp.client import Client

SERVER_URL = "http://localhost:8000/mcp"


def _pretty(value: Any) -> str:
    """Format output in a readable way for quick local testing."""
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


async def smoke_test_mcp_server() -> None:
    """
    Run a simple end-to-end flow to validate MCP server features:
    - connect + ping
    - inspect tools/resources/prompts
    - execute a few known tools when available
    """
    client = Client(SERVER_URL)

    async with client:
        print(f"Connected to: {SERVER_URL}")

        await client.ping()
        print("Ping: OK")

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        tool_names = [tool.name for tool in tools]
        print(f"Tools ({len(tool_names)}): {tool_names}")
        print(f"Resources ({len(resources)}): {[res.uri for res in resources]}")
        print(f"Prompts ({len(prompts)}): {[prompt.name for prompt in prompts]}")

        test_cases: dict[str, dict[str, Any]] = {
            "greet": {"name": "Ford"},
            "calculate": {"expression": "sqrt(16) + 2**3"},
            "web_search": {"query": "Rocscience", "limit": 3},
            "process_image": {
                "image_url": "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg"
            },
        }

        for tool_name, tool_args in test_cases.items():
            if tool_name not in tool_names:
                print(f"[SKIP] {tool_name}: not found on server")
                continue

            try:
                result = await client.call_tool(tool_name, tool_args)
                print(f"[OK] {tool_name}")
                print(_pretty(result))
            except Exception as exc:
                print(f"[FAIL] {tool_name}: {exc}")


if __name__ == "__main__":
    asyncio.run(smoke_test_mcp_server())
