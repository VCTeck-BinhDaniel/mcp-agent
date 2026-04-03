import math
from typing import Annotated

from fastmcp.tools import tool
from fastmcp import Context


@tool()
async def calculate(
    expression: Annotated[
        str,
        "A mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', 'sin(pi/2)')",
    ],
    ctx: Context,
) -> float:
    """
    Evaluate a mathematical expression.
    Supports operators: +, -, *, /, **, %
    Supports math functions: sqrt, sin, cos, tan, log, pi, e, etc.
    Provides a comprehensive capability to calculate any math formula.
    """
    await ctx.debug(f"Evaluating mathematical expression: {expression}")
    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("__")}
    allowed_names.update({"abs": abs, "round": round, "min": min, "max": max})
    try:
        result = float(eval(expression, {"__builtins__": {}}, allowed_names))
        await ctx.info(f"Successfully evaluated '{expression}' = {result}")
        return result
    except Exception as e:
        await ctx.error(f"Failed to evaluate expression '{expression}': {str(e)}")
        raise ValueError(
            f"Failed to evaluate expression '{expression}': {str(e)}"
        ) from e
