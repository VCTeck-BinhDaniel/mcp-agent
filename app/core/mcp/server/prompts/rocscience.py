"""
Prompt: lookup_rocscience_docs

Guides the LLM to look up Rocscience company documentation and answer
the user's question clearly in plain English.
"""

from fastmcp.prompts import prompt
from fastmcp.utilities.logging import get_logger

from app.core.mcp.server.prompts.time_context import now_context_block

logger = get_logger(__name__)


@prompt(
    name="lookup_rocscience_docs",
    description=(
        "Use this prompt when the user asks about Rocscience. "
        "It guides you to fetch the right company info and give a clear, simple answer."
    ),
    tags={"rocscience", "docs", "lookup"},
)
def lookup_rocscience_docs(question: str) -> str:
    """Look up Rocscience documentation and answer the user's question simply."""
    preview = question[:160] + ("…" if len(question) > 160 else "")
    logger.info("prompt lookup_rocscience_docs question_len=%d", len(question))
    logger.debug("prompt lookup_rocscience_docs preview=%r", preview)
    return f"""\
{now_context_block()}

You are a helpful Rocscience assistant.

User question: {question}

Instructions:
1. Call `get_rocscience_info` with the most relevant topic (history / organization / products / strategy / culture / all).
2. If you need more up-to-date or detailed information, call `web_search` or `read_webpage`.
3. Give a clear, concise answer in plain English — no jargon, no bullet-point walls.
4. If something is uncertain, say so briefly.
"""
