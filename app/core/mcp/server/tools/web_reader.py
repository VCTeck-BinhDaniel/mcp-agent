import json
from typing import Annotated, Any

import httpx
from fastmcp import Context
from fastmcp.tools import tool

from app.core.mcp.server.tools.ctx_log import ctx_info
from app.utils.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_JINA_SEARCH_URL = "https://s.jina.ai/"
# Cap tool output so MCP / SSE clients are less likely to time out or drop the connection.
_MAX_SEARCH_CHARS = 200_000
_SEARCH_NEEDS_KEY = (
    "Jina web search requires a valid JINA_API_KEY in your environment or .env file. "
    "read_webpage uses HTTP GET https://r.jina.ai/… which still works without a key for "
    "basic use, but https://s.jina.ai only accepts authenticated requests. "
    "Get a key at https://jina.ai/?sui=apikey"
)


class JinaWebReader:
    """
    A class-based tool provider for Jina AI web services.
    Enables both URL reading and web searching.
    """

    def __init__(self, api_key: str | None = None):
        raw = settings.JINA_API_KEY if api_key is None else api_key
        self.api_key = raw.strip() if isinstance(raw, str) and raw.strip() else None
        self.client_kwargs = {"timeout": 30.0, "follow_redirects": True}
        self._search_client_kwargs = {
            "timeout": httpx.Timeout(120.0, connect=20.0),
            "follow_redirects": True,
        }

    def _get_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        headers: dict[str, str] = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if extra:
            headers.update(extra)
        return headers

    @staticmethod
    def _format_search_hits(items: list[Any]) -> str:
        parts: list[str] = []
        for i, item in enumerate(items, 1):
            if not isinstance(item, dict):
                continue
            title = item.get("title") or "Result"
            url = (item.get("url") or "").strip()
            desc = (item.get("description") or "").strip()
            content = (item.get("content") or "").strip()
            heading = f"## {i}. [{title}]({url})" if url else f"## {i}. {title}"
            blocks = [heading]
            if desc:
                blocks.append(desc)
            if content:
                blocks.append(content)
            parts.append("\n\n".join(blocks))
        return "\n\n---\n\n".join(parts)

    @classmethod
    def _body_from_jina_json(cls, payload: dict[str, Any]) -> str | None:
        data = payload.get("data")
        if isinstance(data, list):
            text = cls._format_search_hits(data)
            return text or None
        if isinstance(data, dict):
            content = data.get("content")
            if isinstance(content, str) and content.strip():
                return content
        return None

    @tool(
        name="read_webpage",
        description="Extract clean markdown content from a specific URL.",
        tags={"reader", "scraping", "jina"},
    )
    async def read_webpage(
        self,
        url: Annotated[str, "The URL of the webpage to read and extract content from"],
        ctx: Context,
    ) -> str:
        """
        Extracts clean, readable Markdown content from a webpage URL using Jina AI.
        Perfect for reading articles, documentation, or extracting text from a website.
        """
        await ctx_info(ctx, f"Extracting webpage content from {url}")
        jina_url = f"https://r.jina.ai/{url}"

        async with httpx.AsyncClient(**self.client_kwargs) as client:
            try:
                response = await client.get(jina_url, headers=self._get_headers())
                response.raise_for_status()
                return response.text
            except httpx.HTTPStatusError as e:
                return (
                    f"HTTP error occurred: {e.response.status_code} - {e.response.text}"
                )
            except Exception as e:
                return f"An unexpected error occurred: {str(e)}"

    @tool(
        name="web_search",
        description=(
            "Search the live web via Jina (GET s.jina.ai, same as official reader flow). "
            "Returns titles, URLs, and short snippets — use read_webpage on a URL for full article text. "
            "Call with `query` (any language); do not claim you searched without calling this tool."
        ),
        tags={"search", "jina", "web"},
    )
    async def web_search(
        self,
        query: Annotated[
            str, "Search keywords or question; Unicode (e.g. Vietnamese) is supported"
        ],
        ctx: Context,
        limit: Annotated[
            int | None,
            "Optional max results (1–10); omit for API default",
        ] = None,
    ) -> str:
        """
        Uses Jina AI Search to find the latest information on the web.
        Returns a concise markdown summary of search results.
        """
        await ctx_info(ctx, f"Searching the web for: {query}")

        if not self.api_key:
            return _SEARCH_NEEDS_KEY

        # Match working Jina usage: GET ?q=... + Bearer + X-Respond-With: no-content.
        # Full per-page markdown via POST can be huge and causes MCP clients to disconnect
        # (ClosedResourceError) before the tool result is delivered.
        params: dict[str, Any] = {"q": query}
        if limit is not None:
            params["num"] = max(1, min(int(limit), 10))

        headers = self._get_headers(
            {
                "Accept": "application/json",
                "X-Respond-With": "no-content",
            }
        )

        async with httpx.AsyncClient(**self._search_client_kwargs) as client:
            try:
                response = await client.get(
                    _JINA_SEARCH_URL,
                    params=params,
                    headers=headers,
                )
                response.raise_for_status()
                ct = (response.headers.get("content-type") or "").lower()
                if "application/json" in ct:
                    payload = response.json()
                    out = self._body_from_jina_json(payload)
                    if out:
                        if len(out) > _MAX_SEARCH_CHARS:
                            out = (
                                out[:_MAX_SEARCH_CHARS]
                                + "\n\n[Output truncated — use read_webpage on a specific URL for full text.]"
                            )
                        return out
                    return json.dumps(payload, ensure_ascii=False)
                text = response.text
                if len(text) > _MAX_SEARCH_CHARS:
                    text = (
                        text[:_MAX_SEARCH_CHARS]
                        + "\n\n[Output truncated — use read_webpage on a specific URL for full text.]"
                    )
                return text
            except httpx.HTTPStatusError as e:
                err_text = e.response.text
                if e.response.status_code == 401:
                    return (
                        "Jina search returned 401: check that JINA_API_KEY is valid "
                        "(read_webpage may still work without a key). "
                        f"Response: {err_text}"
                    )
                return f"HTTP error occurred: {e.response.status_code} - {err_text}"
            except Exception as e:
                return f"An unexpected error occurred: {str(e)}"


# Instantiate the reader
jina_reader = JinaWebReader()
