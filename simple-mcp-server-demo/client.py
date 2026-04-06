import asyncio
import os
import sys
from pathlib import Path

sys.path.append(os.getcwd())

from agents import Agent, ModelSettings, Runner
from agents.mcp import MCPServerStdio
from agents.stream_events import RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent

from app.core.agent.model_provider import llm_model


async def run_chat_loop() -> None:
    current_dir = Path(__file__).resolve().parent
    server_file = current_dir / "mcp_server.py"

    async with MCPServerStdio(
        name="Local Demo MCP Server",
        params={
            "command": "uv",
            "args": ["run", str(server_file)],
        },
    ) as server:
        agent = Agent(
            name="Assistant",
            instructions=(
                "You are a helpful assistant. Use MCP tools, resources, and prompts "
                "from the connected server when they are useful."
            ),
            mcp_servers=[server],
            model=llm_model,
            model_settings=ModelSettings(
                temperature=0.7,
                top_p=0.9,
                tool_choice="auto" if server else None,
            ),
        )

        print("Chat started. Type 'exit' or 'quit' to stop.")
        history: list[dict[str, str]] = []
        while True:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in {"exit", "quit"}:
                print("Goodbye!")
                break

            messages = history + [{"role": "user", "content": user_input}]
            streamed = Runner.run_streamed(agent, input=messages)

            print("Assistant: ", end="", flush=True)
            full_text = ""

            async for event in streamed.stream_events():
                # token deltas
                if event.type == "raw_response_event" and isinstance(
                    event.data, ResponseTextDeltaEvent
                ):
                    chunk = event.data.delta
                    if chunk:
                        full_text += chunk
                        print(chunk, end="", flush=True)

                # tool lifecycle + other high-level events
                elif event.type == "run_item_stream_event":
                    assert isinstance(event, RunItemStreamEvent)

                    if event.name == "tool_called":
                        item = event.item
                        raw = getattr(item, "raw_item", item)
                        tool_name = getattr(raw, "name", None) or getattr(
                            raw, "tool_name", None
                        )
                        tool_input = (
                            getattr(raw, "arguments", None)
                            or getattr(raw, "input", None)
                            or getattr(raw, "params", None)
                        )
                        print(
                            f"\n[tool.called] {tool_name} input={tool_input}\nAssistant: ",
                            end="",
                            flush=True,
                        )

                    elif event.name == "tool_output":
                        item = event.item
                        raw = getattr(item, "raw_item", item)
                        tool_name = getattr(raw, "name", None) or getattr(
                            raw, "tool_name", None
                        )
                        tool_output = getattr(item, "output", None)
                        print(
                            f"\n[tool.output] {tool_name} output={tool_output}\nAssistant: ",
                            end="",
                            flush=True,
                        )

            print("")  # newline after assistant turn
            history.append({"role": "user", "content": user_input})
            history.append({"role": "assistant", "content": full_text})


if __name__ == "__main__":
    asyncio.run(run_chat_loop())
