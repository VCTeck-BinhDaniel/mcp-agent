import asyncio
import json
from pathlib import Path
from typing import Any

from fastmcp.client import Client


def _pretty(value: Any) -> str:
    try:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)
    except Exception:
        return str(value)


async def smoke_test() -> None:
    current_dir = Path(__file__).resolve().parent
    server_file = current_dir / "mcp_server.py"

    client = Client(server_file)

    async with client:
        print(f"Connected to stdio server: {server_file}")
        await client.ping()
        print("Ping: OK")

        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

        print(f"\nTools ({len(tools)}):")
        for tool in tools:
            print(f"- {tool.name}")

        print(f"\nResources ({len(resources)}):")
        for resource in resources:
            print(f"- {resource.uri}")

        print(f"\nPrompts ({len(prompts)}):")
        for prompt in prompts:
            print(f"- {prompt.name}")

        tool_names = {tool.name for tool in tools}
        if "read_resource" in tool_names:
            print("\nTesting tool: read_resource(uri='resource://rocscience')")
            result = await client.call_tool(
                "read_resource", {"uri": "resource://rocscience"}
            )
            print(_pretty(result))
        else:
            print("\n[SKIP] read_resource tool is not available.")


if __name__ == "__main__":
    asyncio.run(smoke_test())
