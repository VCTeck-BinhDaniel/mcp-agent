import json
import os
import random
import sys
from datetime import UTC, datetime
from typing import Annotated

sys.path.append(os.getcwd())

from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastmcp import Context, FastMCP
from fastmcp.server.transforms import PromptsAsTools, ResourcesAsTools
from simple_operators import SAFE_GLOBALS

mcp = FastMCP("test_mcp_server")


@mcp.prompt(
    name="plan_mode",
    description="""
    Force to use them when the user is planning or having a difficult task to implement.
    """,
)
async def plan_mode(ctx: Context) -> str:
    await ctx.info("Planning mode")
    return """
    You are a planning specialist.
    Your job is to carefully read and explore the codebase using only read-only tools (find, grep, cat, ls).
    Do not write, edit, or move any files—planning only. For difficult tasks, analyze requirements and architecture,
    propose a step-by-step implementation plan, discuss trade-offs and dependencies, and anticipate challenges.
    At the end, list 3–5 files as "Critical Files for Implementation". No code, only planning and recommendations.
    """


@mcp.tool(
    name="current_datetime",
    description=(
        "FORCE TO BE USE FOR ANY QUESTION THAT IS RELATED TO TIME, DATE, OR ANYTHING THAT IS TIME-SENSITIVE."
        "Use when the user needs the actual current date, time, weekday, or time-sensitive grounding. "
        "Optionally pass an IANA timezone (e.g. Asia/Ho_Chi_Minh, America/Toronto)."
    ),
    tags={"time", "datetime", "context"},
)
async def current_datetime(
    ctx: Context,
    iana_timezone: Annotated[
        str | None, "The IANA timezone to use for the current datetime"
    ],
) -> str:
    """Return the current UTC, server-local, and optional IANA-zone time."""
    await ctx.info(f"Fetching current datetime with timezone: {iana_timezone}")
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
    name="roll_dice",
    description="Roll a standard six-sided die (D6) and return the result (1-6).",
    tags={"dice", "random", "utility"},
)
async def roll_dice(ctx: Context) -> int:
    """
    Rolls a six-sided die and returns the result.

    Returns:
        int: A random number between 1 and 6.
    """
    result = random.randint(1, 6)
    await ctx.info(f"Rolled a dice and got: {result}")
    return result


mcp.add_transform(PromptsAsTools(mcp))
mcp.add_transform(ResourcesAsTools(mcp))

if __name__ == "__main__":
    mcp.run()
