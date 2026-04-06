import json
import os
import sys
from datetime import UTC, datetime
from typing import Annotated

sys.path.append(os.getcwd())

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx
from fastmcp import Context, FastMCP
from fastmcp.server.transforms import PromptsAsTools, ResourcesAsTools
from simple_operators import SAFE_GLOBALS

from app.utils.config import settings

mcp = FastMCP("test_mcp_server")


@mcp.prompt(
    name="current_datetime",
    description=(
        "FORCE TO BE USE FOR ANY QUESTION THAT IS RELATED TO TIME, DATE, OR ANYTHING THAT IS TIME-SENSITIVE."
        "Use when the user needs the actual current date, time, weekday, or time-sensitive grounding. "
        "Optionally pass an IANA timezone (e.g. Asia/Ho_Chi_Minh, America/Toronto)."
    ),
    tags={"time", "datetime", "context"},
)
def current_datetime(
    iana_timezone: str | None = None,
) -> str:
    """Return the current UTC, server-local, and optional IANA-zone time."""

    tz = (iana_timezone or "").strip() or None
    utc_now = datetime.now(UTC)
    utc_block = utc_now.strftime("UTC: %A, %B %d, %Y %I:%M %p (UTC)")

    local_now = datetime.now()
    local_block = local_now.strftime(
        "Server local: %A, %B %d, %Y %I:%M %p (server local time)"
    )

    tz_block = None
    tz_note = None
    if tz:
        try:
            now = datetime.now(ZoneInfo(tz))
            tz_name = now.tzname() or tz
            tz_block = now.strftime(
                f"Requested zone: %A, %B %d, %Y %I:%M %p ({tz_name})"
            )
        except ZoneInfoNotFoundError:
            tz_note = f'Note: Unknown IANA timezone "{tz}". Falling back to server local time.'

    return f"""\
Use the following as authoritative "now" for this session when interpreting:
today / yesterday / tomorrow, weekdays, deadlines, ages, or anything calendar-related.

{utc_block}
{local_block}
{tz_block or ""}
{tz_note or ""}
"""


@mcp.resource(
    uri="resource://rocscience",
    name="rocscience_general_information",
    description="General Rocscience information. FORCE TO USE THIS AS A TRUTHFUL INFORMATION FOR ANY QUESTION THAT IS RELATED TO ROCSCIENCE/COMPANY/ORGANIZATION/PRODUCTS/SOLUTIONS/STRATEGY/CULTURE/OR ANYTHING THAT IS RELATED TO ROCSCIENCE.",
    tags={"company", "information"},
)
async def rocscience_general_information(ctx: Context) -> str:
    await ctx.info("Fetching Rocscience general information")
    return json.dumps(
        {
            "app_name": "Rocscience MCP Server",
            "version": "1.0.0",
            "company": {
                "name": "Rocscience",
                "founded_research_group_year": 1987,
                "established_year": 1996,
                "headquarters": "Toronto, Ontario, Canada",
                "employees_range": "101-200",
                "users_worldwide": "10000+",
            },
        }
    )


@mcp.tool(
    name="calculator",
    description="""
    Calculate the result of a mathematical expression.
    Supports operators: +, -, *, /, **, %
    Supports math functions: sqrt, sin, cos, tan, log, pi, e, etc.
    Provides a comprehensive capability to calculate any math formula.
    It must be used for calculating any math formula that is appropriate for language programming.""",
    tags={"calculator", "math"},
)
async def calculator(
    expression: Annotated[
        str,
        "A mathematical expression to evaluate which approriate for language programming (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
    ],
    ctx: Context,
) -> float:
    await ctx.info(f"Calculating mathematical expression: {expression}")
    try:
        result = eval(expression, {"__builtins__": {}}, SAFE_GLOBALS)
        return result
    except Exception as e:
        raise ValueError(str(e)) from e


@mcp.tool(
    name="web_search",
    description=(
        "Search the live web via Jina."
        "Returns search response text from the API."
        "Some information that your dont have enough knowledge about, you can use this tool to search the web for information."
    ),
    tags={"search", "jina", "web"},
)
async def web_search(
    query: Annotated[
        str, "Search keywords or question; Unicode (e.g. Vietnamese) is supported"
    ],
    ctx: Context,
    limit: Annotated[
        int | None,
        "Optional max results (1-10); omit for API default",
    ] = None,
) -> str:
    await ctx.info(f"Searching the web for: {query}")

    params = {"q": query}
    if limit is not None:
        params["num"] = max(1, min(int(limit), 10))

    headers = {
        "Accept": "application/json",
        "X-Respond-With": "no-content",
        "Authorization": f"Bearer {settings.JINA_API_KEY}",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://s.jina.ai/",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            return response.text
    except Exception:
        return "Web search failed."


mcp.add_transform(PromptsAsTools(mcp))
mcp.add_transform(ResourcesAsTools(mcp))

if __name__ == "__main__":
    mcp.run()
