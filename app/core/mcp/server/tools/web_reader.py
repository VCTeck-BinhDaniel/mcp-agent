from typing import Annotated

import httpx
from fastmcp import Context
from fastmcp.tools import tool

from app.core.mcp.server.tools.ctx_log import ctx_info
from app.utils.config import settings


@tool(
    name="read_webpage",
    description="Extract clean markdown content from a specific URL.",
    tags={"reader", "scraping", "jina"},
)
async def read_webpage(
    url: Annotated[str, "The URL of the webpage to read and extract content from"],
    ctx: Context,
) -> str:
    """
    Extracts clean, readable Markdown content from a webpage URL using Jina AI.
    Perfect for reading articles, documentation, or extracting text from a website.
    """
    await ctx_info(ctx, f"Extracting webpage content from {url}")
    jina_api_key = settings.JINA_API_KEY
    jina_url = f"https://r.jina.ai/{url}"

    headers = {}
    if jina_api_key:
        headers["Authorization"] = f"Bearer {jina_api_key}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(jina_url, headers=headers)
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError as e:
            return f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting {url}: {str(e)}"
        except Exception as e:
            return f"An unexpected error occurred: {str(e)}"
