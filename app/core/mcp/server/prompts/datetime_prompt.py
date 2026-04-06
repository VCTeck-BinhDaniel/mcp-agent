"""
Prompt: current_datetime

Exposes “now” so the model can ground answers in the real calendar/clock.
"""

from fastmcp.prompts import prompt
from fastmcp.utilities.logging import get_logger

from app.core.mcp.server.prompts.time_context import now_context_block

logger = get_logger(__name__)


@prompt(
    name="current_datetime",
    description=(
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
    logger.info("prompt current_datetime extra_tz=%r", tz)
    block = now_context_block(tz)
    return f"""\
Use the following as authoritative “now” for this session when interpreting:
today / yesterday / tomorrow, weekdays, deadlines, ages, or anything calendar-related.
If the user asked for a specific region, prefer the matching timezone line when present.

{block}
"""
