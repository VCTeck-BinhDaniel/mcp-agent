"""
Tool: get_rocscience_info

Exposes Rocscience company data directly to the LLM as a callable tool
so the agent can answer questions about the company.

Note: MCP *resources* (resources/read) are NOT used here because the
openai-agents-sdk's MCPServerStreamableHttp does not support the resources
protocol. Data is embedded directly from company_data.py instead.
"""

from typing import Annotated, Literal

from fastmcp import Context
from fastmcp.tools import tool

from app.core.mcp.server.resources.company.company_data import (
    CULTURE_AND_COMMUNITY,
    HISTORY_AND_ORIGINS,
    ORGANIZATION_AND_LEADERSHIP,
    PRODUCTS_AND_SOLUTIONS,
    STRATEGY_AND_INNOVATION,
)
from app.core.mcp.server.tools.ctx_log import ctx_info

TopicType = Literal["history", "organization", "products", "strategy", "culture", "all"]

_TOPIC_DATA: dict[str, str] = {
    "history": HISTORY_AND_ORIGINS,
    "organization": ORGANIZATION_AND_LEADERSHIP,
    "products": PRODUCTS_AND_SOLUTIONS,
    "strategy": STRATEGY_AND_INNOVATION,
    "culture": CULTURE_AND_COMMUNITY,
}


@tool(
    name="get_rocscience_info",
    description=(
        "Retrieve information about Rocscience company from the knowledge base. "
        "Use this tool whenever the user asks about Rocscience — its history, products, "
        "leadership, strategy, culture, or any company-related topic. "
        "Pass topic='all' to get a full company overview."
        """
    Available topics:
    - history: Company founding and origins
    - organization: Scale, leadership, global network
    - products: Full product ecosystem
    - strategy: M&A strategy and AI innovation
    - culture: Corporate culture and community
    - all: Complete company overview"""
    ),
    tags={"rocscience", "company", "knowledge"},
)
async def get_rocscience_info(
    topic: Annotated[
        TopicType,
        (
            "The topic to retrieve: "
            "'history' (founding & origins), "
            "'organization' (leadership, scale, financials), "
            "'products' (software products & solutions), "
            "'strategy' (M&A, AI initiatives), "
            "'culture' (corporate culture, community, events), "
            "'all' (full overview of all topics)."
        ),
    ],
    ctx: Context,
) -> str:
    """
    Retrieve Rocscience company information.

    """
    await ctx_info(ctx, f"Fetching Rocscience info: topic='{topic}'")

    topics_to_fetch = list(_TOPIC_DATA.keys()) if topic == "all" else [topic]

    results = [_TOPIC_DATA[t].strip() for t in topics_to_fetch]

    return "\n\n---\n\n".join(results)
