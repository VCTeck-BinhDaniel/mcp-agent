import logging
import os
import sys
from pathlib import Path

sys.path.append(os.getcwd())

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from fastmcp.utilities.logging import get_logger
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Column, Heading, Row, Text

from app.core.mcp.server.resources.company.server import company_server

to_client_logger = get_logger(name="fastmcp.server.context.to_client")
to_client_logger.setLevel(level=logging.DEBUG)


provider = FileSystemProvider(
    root=Path(__file__).parent / "tools",
    reload=True,
)

mcp = FastMCP("Rocscience MCP Server", providers=[provider])

# Mount sub-servers
mcp.mount(company_server, namespace="company")


@mcp.tool(app=True)
def greet(name: str) -> PrefabApp:
    """Greet someone with a visual card."""
    with Column(gap=4, css_class="p-6") as view:
        Heading(f"Hello, {name}!")
        with Row(gap=2, align="center"):
            Text("Status")
            Badge("Greeted", variant="success")

    return PrefabApp(view=view)


if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
