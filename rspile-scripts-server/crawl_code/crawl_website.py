"""Crawl RSPile scripting examples: index links under section#model, then fetch each page."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

EXAMPLES_INDEX_URL = "https://rocscience.github.io/rspile-scripting/examples.html"
REQUEST_TIMEOUT_S = 60
USER_AGENT = (
    "Mozilla/5.0 (compatible; RSPileDocsCrawler/1.0; +https://rocscience.github.io/)"
)
HTTP_HEADERS = {"User-Agent": USER_AGENT}


@dataclass(frozen=True)
class ExamplePageData:
    """Extracted content from one example documentation page."""

    url: str
    h1: str
    paragraphs_html: list[str]
    code_blocks: list[str]


def _http_timeout() -> httpx.Timeout:
    return httpx.Timeout(REQUEST_TIMEOUT_S)


async def fetch_html(client: httpx.AsyncClient, url: str) -> str:
    r = await client.get(url)
    r.raise_for_status()
    return r.text


def collect_model_section_links(index_html: str, base_url: str) -> list[str]:
    """Return absolute URLs for every ``li > a.reference.internal`` under ``section#model``."""
    soup = BeautifulSoup(index_html, "html.parser")
    section = soup.find("section", id="model")
    if section is None:
        msg = 'No <section id="model"> found on examples index page'
        raise ValueError(msg)

    hrefs: list[str] = []
    for a in section.select("li a.reference.internal[href]"):
        href = a.get("href", "").strip()
        if not href or href.startswith("#"):
            continue
        hrefs.append(urljoin(base_url, href))

    seen: set[str] = set()
    unique: list[str] = []
    for u in hrefs:
        if u not in seen:
            seen.add(u)
            unique.append(u)
    return unique


def _strip_headerlinks(soup_fragment: BeautifulSoup) -> None:
    for a in soup_fragment.select("a.headerlink"):
        a.decompose()


def extract_example_page(article_html: BeautifulSoup, page_url: str) -> ExamplePageData:
    """Parse main article: h1 text, all ``<p>`` outer HTML, and all highlighted code blocks."""
    article = article_html.select_one("article.bd-article")
    if article is None:
        article = article_html

    h1_el = article.select_one("h1")
    h1_text = ""
    if h1_el is not None:
        h1_copy = BeautifulSoup(str(h1_el), "html.parser")
        h1_inner = h1_copy.find("h1")
        if h1_inner is not None:
            _strip_headerlinks(h1_inner)
            h1_text = h1_inner.get_text(strip=True)

    paragraphs_html: list[str] = []
    for p in article.select("p"):
        paragraphs_html.append(str(p))

    code_blocks: list[str] = []
    for pre in article.select("div.highlight pre"):
        code_blocks.append(pre.get_text())

    return ExamplePageData(
        url=page_url,
        h1=h1_text,
        paragraphs_html=paragraphs_html,
        code_blocks=code_blocks,
    )


async def _fetch_example_page(
    client: httpx.AsyncClient,
    link: str,
) -> ExamplePageData:
    html = await fetch_html(client, link)
    soup = BeautifulSoup(html, "html.parser")
    return extract_example_page(soup, link)


async def crawl_examples_async(
    index_url: str = EXAMPLES_INDEX_URL,
) -> list[ExamplePageData]:
    """Fetch index, discover links under ``section#model``, then fetch all example pages in parallel."""
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    async with httpx.AsyncClient(
        headers=HTTP_HEADERS,
        timeout=_http_timeout(),
        follow_redirects=True,
        limits=limits,
    ) as client:
        index_html = await fetch_html(client, index_url)
        parsed = urlparse(index_url)
        base = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}/"
        links = collect_model_section_links(index_html, base)

        tasks = [_fetch_example_page(client, link) for link in links]
        return list(await asyncio.gather(*tasks))


def crawl_examples(index_url: str = EXAMPLES_INDEX_URL) -> list[ExamplePageData]:
    """Sync entry: runs async parallel crawl in one event loop."""
    return asyncio.run(crawl_examples_async(index_url=index_url))


def _serialize_results(rows: list[ExamplePageData]) -> list[dict[str, Any]]:
    return [asdict(r) for r in rows]


def main() -> None:
    out_path = "crawled_examples.json"
    rows = crawl_examples()
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(_serialize_results(rows), f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
