"""
Safe Context logging helpers for FastMCP tools.

Background
----------
fastmcp `ctx.info/debug/warning/error()` internally call `send_nowait` on an
anyio MemoryObjectSendStream to push log notifications to the MCP client.

When the openai-agents-sdk client (MCPServerStreamableHttp) receives a tool
result it immediately closes the connection (DELETE /mcp).  If a subsequent
ctx log call fires *after* that close, anyio raises `ClosedResourceError`,
which propagates through the session TaskGroup and crashes the entire session.

These helpers swallow transport-layer exceptions so ctx logging is always safe
to use inside tools, while still relying on the server-side
`fastmcp.server.context.to_client` logger for observability.

See `.docs/server/logging.md`: client-visible logs use ctx.*; fallback uses
FastMCP's server-side get_logger (not the app-wide logger).
"""

from fastmcp import Context
from fastmcp.utilities.logging import get_logger

logger = get_logger(__name__)


async def ctx_debug(ctx: Context, message: str, **kwargs) -> None:
    try:
        await ctx.debug(message, **kwargs)
    except Exception:
        logger.debug(message)


async def ctx_info(ctx: Context, message: str, **kwargs) -> None:
    try:
        await ctx.info(message, **kwargs)
    except Exception:
        logger.info(message)


async def ctx_warning(ctx: Context, message: str, **kwargs) -> None:
    try:
        await ctx.warning(message, **kwargs)
    except Exception:
        logger.warning(message)


async def ctx_error(ctx: Context, message: str, **kwargs) -> None:
    try:
        await ctx.error(message, **kwargs)
    except Exception:
        logger.error(message)
