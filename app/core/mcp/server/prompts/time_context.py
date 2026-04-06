"""Shared current-time text for MCP prompts (models have no built-in clock)."""

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def now_context_block(iana_timezone: str | None = None) -> str:
    """
    Return a short, human-readable time snapshot.

    Args:
        iana_timezone: Optional IANA name (e.g. ``America/Toronto``, ``Asia/Ho_Chi_Minh``).
    """
    utc = datetime.now(ZoneInfo("UTC"))
    lines = [
        f"- UTC: {utc.strftime('%Y-%m-%d %H:%M:%S')} (ISO {utc.isoformat(timespec='seconds')})",
    ]

    local = datetime.now().astimezone()
    lines.append(f"- Server local: {local.isoformat(timespec='seconds')}")

    if iana_timezone:
        try:
            tz = ZoneInfo(iana_timezone)
            t = datetime.now(tz)
            zn = t.tzname() or ""
            lines.append(
                f"- {iana_timezone}: {t.strftime('%Y-%m-%d %H:%M:%S')} {zn}".rstrip()
            )
        except ZoneInfoNotFoundError:
            lines.append(f"- (unknown IANA timezone: {iana_timezone!r})")

    return "Current reference time:\n" + "\n".join(lines)
