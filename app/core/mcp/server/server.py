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

# NOTE: MCP resources are disabled — openai-agents-sdk does not support the
# resources/read protocol. Company data is embedded directly in the tool.
# from app.core.mcp.server.resources.company.company_data import (
#     CULTURE_AND_COMMUNITY,
#     HISTORY_AND_ORIGINS,
#     ORGANIZATION_AND_LEADERSHIP,
#     PRODUCTS_AND_SOLUTIONS,
#     STRATEGY_AND_INNOVATION,
# )

to_client_logger = get_logger(name="fastmcp.server.context.to_client")
to_client_logger.setLevel(level=logging.DEBUG)


provider = FileSystemProvider(
    root=Path(__file__).parent / "tools",
    reload=True,
)

mcp = FastMCP("Rocscience MCP Server", providers=[provider])


# ── Company resources (disabled: openai-agents-sdk does not support MCP resources) ──

# @mcp.resource("rocscience://company/history")
# def company_history() -> str:
#     """Get Rocscience history and origins."""
#     return HISTORY_AND_ORIGINS.strip()


# @mcp.resource("rocscience://company/organization")
# def company_organization() -> str:
#     """Get Rocscience organization info, scale, and leadership."""
#     return ORGANIZATION_AND_LEADERSHIP.strip()


# @mcp.resource("rocscience://company/products")
# def company_products() -> str:
#     """Get Rocscience product ecosystem details."""
#     return PRODUCTS_AND_SOLUTIONS.strip()


# @mcp.resource("rocscience://company/strategy")
# def company_strategy() -> str:
#     """Get Rocscience M&A strategy and innovation initiatives."""
#     return STRATEGY_AND_INNOVATION.strip()


# @mcp.resource("rocscience://company/culture")
# def company_culture() -> str:
#     """Get Rocscience corporate culture and community events."""
#     return CULTURE_AND_COMMUNITY.strip()


# ── UI tools ─────────────────────────────────────────────────────────────────


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
    mcp.run(transport="http", host="0.0.0.0", port=6969)
