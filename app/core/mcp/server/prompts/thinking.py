"""
Prompt: think_step_by_step

Guides the LLM through a simple thinking process before answering,
so the final response is clear, accurate, and easy to understand.
"""

from fastmcp.prompts import Message, prompt
from fastmcp.utilities.logging import get_logger

from app.core.mcp.server.prompts.time_context import now_context_block

logger = get_logger(__name__)


@prompt(
    name="think_step_by_step",
    description=(
        "Use this prompt for any question that needs a bit of reasoning before answering. "
        "It asks the LLM to think through the problem first, then give a simple final answer."
    ),
    tags={"reasoning", "thinking", "assistant"},
)
def think_step_by_step(question: str) -> list[Message]:
    """Think through a question step by step, then give a clear simple answer."""
    preview = question[:160] + ("…" if len(question) > 160 else "")
    logger.info("prompt think_step_by_step question_len=%d", len(question))
    logger.debug("prompt think_step_by_step preview=%r", preview)
    return [
        Message(
            f"""\
{now_context_block()}

Think through this carefully before answering.

Question: {question}

Step 1 — Understand: What is the user really asking?
Step 2 — Gather: What information or tools do I need?
Step 3 — Reason: What is the most accurate answer?
Step 4 — Simplify: How do I explain it clearly in plain English?

Now give your final answer — short, direct, and easy to understand.
"""
        ),
    ]
