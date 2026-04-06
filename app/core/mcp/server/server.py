import logging
import os
import sys
from pathlib import Path

sys.path.append(os.getcwd())

from fastmcp import FastMCP
from fastmcp.server.providers import FileSystemProvider
from fastmcp.server.transforms import PromptsAsTools, ResourcesAsTools
from fastmcp.utilities.logging import get_logger
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Column, Heading, Row, Text

from app.core.mcp.server.prompts.datetime_prompt import current_datetime
from app.core.mcp.server.prompts.rocscience import lookup_rocscience_docs
from app.core.mcp.server.prompts.thinking import think_step_by_step
from app.core.mcp.server.resources.company.server import company_server
from app.core.mcp.server.tools.web_reader import jina_reader

# MCP client logs (ctx.debug/info/...) also go to this logger at DEBUG — see .docs/server/logging.md
to_client_logger = get_logger(name="fastmcp.server.context.to_client")
to_client_logger.setLevel(level=logging.DEBUG)


provider = FileSystemProvider(
    root=Path(__file__).parent / "tools",
    reload=True,
)

mcp = FastMCP("Rocscience MCP Server", providers=[provider])

# ── Tools ────────────────────────────────────────────────────────────────────

mcp.add_tool(jina_reader.read_webpage)
mcp.add_tool(jina_reader.web_search)

# ── Resources (company data) ──────────────────────────────────────────────────
# Full MCP clients use resources/read. Tool-only clients use read_resource via
# ResourcesAsTools (below). URIs: rocscience://company/* from company_server.

mcp.mount(company_server)

# ── Prompts ───────────────────────────────────────────────────────────────────

mcp.add_prompt(lookup_rocscience_docs)
mcp.add_prompt(think_step_by_step)
mcp.add_prompt(current_datetime)

# ── Tool-only clients (e.g. openai-agents-sdk) ────────────────────────────────
# Exposes list_prompts / get_prompt and list_resources / read_resource as tools.

mcp.add_transform(PromptsAsTools(mcp))
mcp.add_transform(ResourcesAsTools(mcp))


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
