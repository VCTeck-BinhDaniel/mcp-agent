"""AI agent service.

SSE event types produced:
    agent.message.delta        – text chunk arriving from the model
    agent.message.done         – full response complete; carries session_id
    agent.workflow.failed      – unhandled exception

    # RunItemStreamEvent (high-level, item-complete signals)
    agent.tool.called          – MCP/function tool was invoked; carries name + input
    agent.tool.output          – tool result returned; carries name + output
    agent.tool_search.called   – hosted tool-search request issued
    agent.tool_search.output   – hosted tool-search results loaded
    agent.mcp.list_tools       – client listed MCP tools
    agent.mcp.approval_requested – MCP tool needs human approval
    agent.mcp.approval_response  – approval decision recorded
    agent.handoff.requested    – handoff was requested by the model
    agent.handoff.occurred     – handoff to a new agent completed
    agent.reasoning.created    – reasoning/thinking item produced
    agent.updated              – AgentUpdatedStreamEvent (agent switched)
"""

import logging
import uuid
from contextlib import AsyncExitStack

from agents import Agent, ItemHelpers, ModelSettings, Runner
from agents.mcp import MCPServerStreamableHttp
from agents.stream_events import AgentUpdatedStreamEvent, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent

from app.utils.config import settings
from app.utils.serializer import make_sse_event

from .model_provider import llm_model

logger = logging.getLogger(__name__)

_INSTRUCTIONS = (
    "You are a helpful, friendly, and concise AI assistant. "
    "Answer clearly and accurately. If you don't know something, say so.\n\n"
    "You have MCP tools including `web_search` (live web search) and `read_webpage` (fetch one URL). "
    "When the user asks for news, current facts, or anything that depends on the public internet, "
    "you MUST call `web_search` with a focused `query` (any language, e.g. Vietnamese) BEFORE you answer. "
    "Do not say you are searching or pretend to have search results without actually invoking `web_search`. "
    "After you receive tool output, summarize it for the user and cite key sources when helpful."
)


# {"role": "user"|"assistant", "content": str}
HistoryMessage = dict[str, str]


class ChatAgent:
    def __init__(self) -> None:
        self._exit_stack = AsyncExitStack()
        self._mcp_server = None
        # We delay initialization of self._agent until initialize() is called
        self._agent = None

    async def initialize(self) -> None:
        """Initialize the MCP server connection and the AI Agent context."""
        mcp_servers = []

        mcp_url = settings.MCP_SERVER_URL
        if mcp_url:
            try:
                headers = {}
                if settings.MCP_SERVER_TOKEN:
                    headers["Authorization"] = f"Bearer {settings.MCP_SERVER_TOKEN}"

                # Using cache_tools_list=True as an optimization to avoid reloading tools on every call
                self._mcp_server = await self._exit_stack.enter_async_context(
                    MCPServerStreamableHttp(
                        name="FastMCP HTTP Server",
                        params={
                            "url": mcp_url,
                            "headers": headers,
                            "timeout": 10,
                        },
                        cache_tools_list=True,
                        max_retry_attempts=3,
                    )
                )
                mcp_servers.append(self._mcp_server)
                logger.info("Successfully connected to MCP Server at %s", mcp_url)
            except Exception as exc:
                logger.error("Failed to connect to MCP Server: %s", exc)

        # NOTE: Gemini API (OpenAI-compatible endpoint) returns 400 if tool_choice is set
        # but function_declarations is empty (i.e. no MCP tools available).
        # Only enable tool_choice="auto" when we have actual MCP servers connected.
        model_settings = ModelSettings(
            temperature=0.7,
            top_p=0.9,
            tool_choice="auto" if mcp_servers else None,
        )

        self._agent = Agent(
            name="AI Assistant",
            instructions=_INSTRUCTIONS,
            model=llm_model,
            model_settings=model_settings,
            mcp_servers=mcp_servers,
        )
        logger.info(
            "Agent initialized with %d MCP server(s), tool_choice=%s",
            len(mcp_servers),
            "auto" if mcp_servers else "None (no tools)",
        )

    async def shutdown(self) -> None:
        """Close the MCP server connection gracefully."""
        await self._exit_stack.aclose()
        logger.info("Agent resources safely shut down.")

    async def stream_response(
        self,
        user_message: str,
        history: list[HistoryMessage],
        session_id: uuid.UUID,
        result_holder: list[str] | None = None,
    ):
        """Async generator that yields SSE-formatted strings.

        Args:
            user_message:  The current user's message.
            history:       Prior conversation turns (excluding the current message).
            session_id:    Echoed back in the ``agent.message.done`` payload per spec.
            result_holder: If provided, the full assistant response is appended here
                           after streaming completes so callers can persist it without
                           re-parsing SSE strings.

        Yields:
            SSE strings ready to be forwarded via FastAPI StreamingResponse.
        """
        if self._agent is None:
            yield make_sse_event(
                "agent.workflow.failed", {"error": "Agent not initialized"}
            )
            return

        messages = history + [{"role": "user", "content": user_message}]
        full_response = ""

        _EMPTY_OUTPUT_MSG = "model output must contain either output text or tool calls"

        try:
            result = Runner.run_streamed(self._agent, input=messages)

            async for event in result.stream_events():
                # ── raw token delta ────────────────────────────────────────
                if event.type == "raw_response_event" and isinstance(
                    event.data, ResponseTextDeltaEvent
                ):
                    chunk = event.data.delta
                    if chunk:
                        full_response += chunk
                        yield make_sse_event("agent.message.delta", {"text": chunk})

                # ── high-level item events ─────────────────────────────────
                elif event.type == "run_item_stream_event":
                    assert isinstance(event, RunItemStreamEvent)
                    name = event.name
                    item = event.item

                    if name == "message_output_created":
                        full_response = ItemHelpers.text_message_output(item)

                    elif name == "tool_called":
                        raw = getattr(item, "raw_item", item)
                        yield make_sse_event(
                            "agent.tool.called",
                            {
                                "tool": getattr(raw, "name", None),
                                "input": getattr(raw, "arguments", None)
                                or getattr(raw, "input", None)
                                or getattr(raw, "params", None),
                            },
                        )

                    elif name == "tool_output":
                        raw = getattr(item, "raw_item", item)
                        yield make_sse_event(
                            "agent.tool.output",
                            {
                                "tool": getattr(raw, "name", None)
                                or getattr(raw, "tool_name", None),
                                "output": getattr(item, "output", None),
                            },
                        )

                    elif name == "tool_search_called":
                        yield make_sse_event(
                            "agent.tool_search.called",
                            {"query": getattr(item, "query", None)},
                        )

                    elif name == "tool_search_output_created":
                        yield make_sse_event(
                            "agent.tool_search.output",
                            {"results": getattr(item, "results", None)},
                        )

                    elif name == "mcp_list_tools":
                        tool_names = [
                            t.name if hasattr(t, "name") else str(t)
                            for t in getattr(item, "tools", [])
                        ]
                        yield make_sse_event(
                            "agent.mcp.list_tools",
                            {"tools": tool_names},
                        )

                    elif name == "mcp_approval_requested":
                        yield make_sse_event(
                            "agent.mcp.approval_requested",
                            {
                                "tool": getattr(item, "tool_name", None),
                                "input": getattr(item, "arguments", None),
                            },
                        )

                    elif name == "mcp_approval_response":
                        yield make_sse_event(
                            "agent.mcp.approval_response",
                            {"approved": getattr(item, "approve", None)},
                        )

                    elif name in ("handoff_requested", "handoff_occured"):
                        sse_name = (
                            "agent.handoff.requested"
                            if name == "handoff_requested"
                            else "agent.handoff.occurred"
                        )
                        yield make_sse_event(
                            sse_name,
                            {"target": getattr(item, "target_agent", {})},
                        )

                    elif name == "reasoning_item_created":
                        yield make_sse_event(
                            "agent.reasoning.created",
                            {"reasoning": getattr(item, "content", None)},
                        )

                # ── agent-switch event ─────────────────────────────────────
                elif event.type == "agent_updated_stream_event":
                    assert isinstance(event, AgentUpdatedStreamEvent)
                    yield make_sse_event(
                        "agent.updated",
                        {"agent": event.new_agent.name},
                    )

        except Exception as exc:
            err_str = str(exc)
            # Gemini (OpenAI-compatible) occasionally returns an empty completion
            # after tool results — the SDK raises UserError with this message.
            # Surface a friendly fallback instead of an ugly error.
            if _EMPTY_OUTPUT_MSG in err_str:
                logger.warning(
                    "Gemini returned empty model output (known issue with tool calls). "
                    "Yielding fallback message."
                )
                fallback = "Tôi đã thực hiện xong yêu cầu của bạn. Bạn có muốn biết thêm điều gì không?"
                full_response = fallback
                yield make_sse_event("agent.message.delta", {"text": fallback})
            else:
                logger.exception("Agent run failed: %s", exc)
                yield make_sse_event("agent.workflow.failed", {"error": err_str})
                return

        if result_holder is not None:
            result_holder.append(full_response)

        yield make_sse_event("agent.message.done", {"session_id": str(session_id)})


# Module-level singleton – import and use directly
agent = ChatAgent()
