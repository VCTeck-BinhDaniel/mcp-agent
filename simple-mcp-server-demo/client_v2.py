import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Any

sys.path.append(os.getcwd())

from fastmcp.client import Client
from openai import OpenAI

from app.utils.config import settings

mcp_client = Client(transport="simple-mcp-server-demo/mcp_server.py")
# openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = OpenAI(
    api_key=settings.GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)


async def main():
    async with mcp_client:
        await mcp_client.ping()

        mcp_tools = await mcp_client.list_tools()
        # resources = await mcp_client.list_resources()
        # prompts = await mcp_client.list_prompts()

        def mcp_tools_to_openai_tools(mcp_tools: list[Any]):
            tools = []
            for tool in mcp_tools:
                # for key in vars(tool):
                #     print(f"{key} = {getattr(tool, key)}")
                # print("--------------------------------")

                schema = getattr(tool, "inputSchema", None) or (
                    {"type": "object", "properties": {}, "required": []}
                )
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                "type": "object",
                                "properties": schema.get("properties", {}),
                                "required": schema.get("required", []),
                                "additionalProperties": schema.get(
                                    "additionalProperties", False
                                ),
                            },
                        },
                    }
                )
            return tools

        openai_tools = mcp_tools_to_openai_tools(mcp_tools)

        conversation_history = [
            {
                "role": "system",
                "content": (
                    "You are an assistant that MUST use available tools whenever the user's request is related to company information, calculations, "
                    "or when a tool is needed for an accurate answer. Do NOT answer from prior knowledge—always call a relevant tool for such cases. "
                ),
            }
        ]
        print("How can I help you today? Type 'quit' to exit.")

        while True:
            user_prompt = input("> ")
            if user_prompt == "quit":
                break

            conversation_history.append({"role": "user", "content": user_prompt})

            while True:
                response = gemini_client.chat.completions.create(
                    model=settings.GEMINI_MODEL,
                    messages=conversation_history,
                    tools=openai_tools,
                    tool_choice="auto",
                    extra_body={
                        "extra_body": {
                            "google": {
                                "thinking_config": {
                                    "thinking_level": "low",
                                    "include_thoughts": True,
                                }
                            }
                        }
                    },
                )
                msg = response.choices[0].message
                if msg.content:
                    print(msg.content, end="\n", flush=True)
                if not msg.tool_calls:
                    conversation_history.append(
                        {"role": "assistant", "content": msg.content}
                    )
                    break
                print(
                    "Tool calls:",
                    [
                        f"name:{tc.function.name}, arguments:{tc.function.arguments or '{}'}"
                        for tc in msg.tool_calls
                    ],
                )
                assistant_turn: dict[str, Any] = {
                    "role": "assistant",
                    "content": (msg.content if msg.content else ""),
                }
                # Handle the parallel tool calls
                for i, tc in enumerate(msg.tool_calls):
                    if i == 0:
                        assistant_turn["tool_calls"] = [
                            {
                                "extra_content": {
                                    "google": {
                                        "thought_signature": tc.extra_content.get(
                                            "google", {}
                                        ).get("thought_signature", ""),
                                    },
                                },
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments or "{}",
                                },
                            }
                        ]
                    else:
                        assistant_turn["tool_calls"].append(
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments or "{}",
                                },
                            }
                        )

                conversation_history.append(assistant_turn)
                for tc in msg.tool_calls:
                    tool_name = tc.function.name
                    tool_args = json.loads(tc.function.arguments or "{}")
                    raw = await mcp_client.call_tool(tool_name, tool_args)
                    conversation_history.append(
                        {
                            "role": "tool",
                            "name": tool_name,
                            "tool_call_id": tc.id,
                            "content": json.dumps(
                                raw.structured_content, ensure_ascii=False
                            ),
                        }
                    )

        print("The chatbot has been shut down.")

        filename = "conversation_history.json"
        conversation_data = {
            "filename": datetime.now().isoformat(),
            "history": conversation_history,
        }

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(conversation_data, f, ensure_ascii=False, indent=2)

        print(f"Conversation history saved to {filename}")


asyncio.run(main())
