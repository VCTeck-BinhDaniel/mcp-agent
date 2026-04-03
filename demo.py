import json
import os
import uuid

import requests
import streamlit as st

st.set_page_config(page_title="AI Chat Demo", page_icon="🤖", layout="centered")

st.title("🤖 AI Chat Service Demo")
st.markdown(
    "A fast Streamlit frontend connecting to the FastAPI backend with streaming."
)

# Allow configuring the backend URL (useful for local vs docker)
API_URL = os.getenv("API_URL", "http://localhost:8000")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    if "user_id" not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    user_id = st.text_input("User ID", value=st.session_state.user_id)
    session_id = st.text_input("Session ID", value=st.session_state.session_id)
    st.caption(
        "⚠️ Session ID phải là UUID hợp lệ (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)"
    )
    st.markdown(f"**Backend URL:** `{API_URL}`")

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ── Chat history ──────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        for meta in message.get("tool_calls", []):
            with st.expander(f"🔧 Tool: `{meta['tool']}`", expanded=False):
                if meta.get("input"):
                    st.json(meta["input"])
                if meta.get("output"):
                    st.markdown("**Output:**")
                    st.code(str(meta["output"]))

# ── SSE event parser ──────────────────────────────────────────────────────────


def _parse_sse_events(response: requests.Response):
    """Low-level SSE line parser — yields (event_name, data_dict) tuples."""
    current_event = None
    for raw_line in response.iter_lines():
        if not raw_line:
            current_event = None
            continue
        line = raw_line.decode("utf-8")
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data: "):
            try:
                yield current_event, json.loads(line[6:])
            except json.JSONDecodeError:
                continue


# ── Main streaming function ───────────────────────────────────────────────────


def _sse_stream_generator(response: requests.Response, tool_calls: list, status_ph):
    """
    Generator consumed by st.write_stream.
    Yields text chunks for display while handling side-effect events inline.
    """
    _current_tool: dict | None = None

    for event, data in _parse_sse_events(response):
        # ── text delta: yield to st.write_stream ─────────────────────────────
        if event == "agent.message.delta":
            chunk = data.get("text", "")
            if chunk:
                status_ph.empty()
                yield chunk

        # ── tool called ──────────────────────────────────────────────────────
        elif event == "agent.tool.called":
            tool_name = data.get("tool", "unknown")
            tool_input = data.get("input")
            _current_tool = {"tool": tool_name, "input": tool_input, "output": None}
            tool_calls.append(_current_tool)
            status_ph.status(f"⚙️ Calling tool `{tool_name}`…", state="running")

        # ── tool output ──────────────────────────────────────────────────────
        elif event == "agent.tool.output":
            tool_output = data.get("output")
            if _current_tool:
                _current_tool["output"] = tool_output
            status_ph.empty()

        # ── MCP tool list ────────────────────────────────────────────────────
        elif event == "agent.mcp.list_tools":
            tools = data.get("tools", [])
            status_ph.info(f"🔌 MCP tools available: {', '.join(tools)}")

        # ── MCP approval ─────────────────────────────────────────────────────
        elif event == "agent.mcp.approval_requested":
            tool_name = data.get("tool", "?")
            status_ph.warning(f"🔐 MCP approval requested for tool **{tool_name}**")

        elif event == "agent.mcp.approval_response":
            approved = data.get("approved")
            status_ph.info(f"✅ Approval {'granted' if approved else 'denied'}")

        # ── hosted tool search ───────────────────────────────────────────────
        elif event == "agent.tool_search.called":
            query = data.get("query", "")
            status_ph.status(f"🔍 Searching: `{query}`…", state="running")

        elif event == "agent.tool_search.output":
            status_ph.empty()

        # ── handoff ──────────────────────────────────────────────────────────
        elif event in ("agent.handoff.requested", "agent.handoff.occurred"):
            target = data.get("target") or {}
            name = (
                target.get("name", "another agent")
                if isinstance(target, dict)
                else str(target)
            )
            label = "Handing off" if "requested" in event else "Handed off"
            status_ph.info(f"🔀 {label} to **{name}**")

        # ── reasoning ────────────────────────────────────────────────────────
        elif event == "agent.reasoning.created":
            reasoning = data.get("reasoning", "")
            if reasoning:
                with st.expander("🧠 Reasoning", expanded=False):
                    st.markdown(reasoning)

        # ── agent updated ────────────────────────────────────────────────────
        elif event == "agent.updated":
            agent_name = data.get("agent", "")
            status_ph.info(f"🤖 Switched to agent: **{agent_name}**")

        # ── workflow failed ──────────────────────────────────────────────────
        elif event == "agent.workflow.failed":
            raise RuntimeError(data.get("error", "Unknown error"))


def render_stream(prompt: str, session_id: str, user_id: str):
    """
    Consumes the SSE stream and renders everything live in Streamlit.
    Uses st.write_stream for smooth token-by-token text display.

    Returns:
        full_response (str): the complete assistant text
        tool_calls (list):   list of {tool, input, output} dicts for history
    """
    payload = {"message": prompt, "session_id": session_id, "user_id": user_id}

    tool_calls: list[dict] = []
    status_ph = st.empty()  # live status line (tool running…)

    with requests.post(
        f"{API_URL}/api/v1/chat/stream",
        json=payload,
        stream=True,
        timeout=120,
    ) as response:
        response.raise_for_status()

        # st.write_stream consumes the generator and returns the full text
        full_response = st.write_stream(
            _sse_stream_generator(response, tool_calls, status_ph)
        )

    status_ph.empty()

    # Show tool call expanders under the response
    for tc in tool_calls:
        with st.expander(f"🔧 Tool: `{tc['tool']}`", expanded=False):
            if tc.get("input"):
                st.json(tc["input"])
            if tc.get("output"):
                st.markdown("**Output:**")
                st.code(str(tc["output"]))

    return full_response or "", tool_calls


# ── Chat input ────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask something..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            full_response, tool_calls = render_stream(prompt, session_id, user_id)
        except RuntimeError as e:
            st.error(f"⚠️ Error: {e}")
            full_response, tool_calls = "", []
        except requests.exceptions.RequestException as e:
            st.error(f"⚠️ Cannot reach backend: {e}")
            full_response, tool_calls = "", []

    if full_response:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": full_response,
                "tool_calls": tool_calls,
            }
        )
