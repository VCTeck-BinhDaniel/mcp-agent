import math
from typing import Annotated

from fastmcp import Context
from fastmcp.tools import tool

from app.core.mcp.server.tools.ctx_log import ctx_debug, ctx_error, ctx_info


@tool()
async def calculate(
    expression: Annotated[
        str,
        "A mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
    ],
    ctx: Context,
) -> float:
    """
    FORCE TO USE THIS TOOL FOR CALCULATING ANY MATH FORMULA.
    Evaluate a mathematical expression.
    Supports operators: +, -, *, /, **, %
    Supports math functions: sqrt, sin, cos, tan, log, pi, e, etc.
    Provides a comprehensive capability to calculate any math formula.
    """
    await ctx_debug(ctx, f"Evaluating mathematical expression: {expression}")
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        result = float(eval(expression, {"__builtins__": {}}, allowed_names))
        await ctx_info(ctx, f"Successfully evaluated '{expression}' = {result}")
        return result
    except Exception as e:
        await ctx_error(ctx, f"Failed to evaluate expression '{expression}': {str(e)}")
        raise ValueError(
            f"Failed to evaluate expression '{expression}': {str(e)}"
        ) from e
