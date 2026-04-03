import base64
from typing import Annotated

import httpx
from fastmcp import Context
from fastmcp.tools import tool


@tool()
async def process_image(
    image_url: Annotated[str, "URL of the image to fetch and process"],
    ctx: Context,
) -> dict:
    """Fetch an image from a URL and convert it to Base64 format so the AI can easily understand it."""
    await ctx.info(f"Fetching image from {image_url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                image_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) MCP-Agent/1.0"
                },
            )
            response.raise_for_status()

            image_bytes = response.content
            content_type = response.headers.get(
                "content-type", "application/octet-stream"
            )

            base64_encoded = base64.b64encode(image_bytes).decode("utf-8")

            await ctx.debug(
                "Image fetched and encoded successfully",
                extra={"mime_type": content_type, "length": len(image_bytes)},
            )

            return {
                "status": "success",
                "source_url": image_url,
                "mime_type": content_type,
                "base64_data": base64_encoded,
                "data_uri": f"data:{content_type};base64,{base64_encoded}",
            }
    except Exception as e:
        await ctx.error(f"Failed to fetch or process image: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to fetch or process image: {str(e)}",
        }
