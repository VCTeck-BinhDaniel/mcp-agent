"""Download example model files linked from ``crawled_examples.json`` into ``ExampleCode/``."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import unquote, urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT_S = 120
USER_AGENT = "Mozilla/5.0 (compatible; RSPileExampleInstaller/1.0; +https://rocscience.github.io/)"


def github_blob_url_to_raw(url: str) -> str:
    """Turn ``https://github.com/org/repo/blob/branch/path`` into a raw.githubusercontent URL."""
    parsed = urlparse(url)
    if parsed.netloc != "github.com":
        return url
    parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(parts) < 5 or parts[2] != "blob":
        return url
    user, repo, _blob, branch, *rest = parts
    if not rest:
        return url
    tail = "/".join(rest)
    return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{tail}"


def _safe_filename(name: str) -> str:
    for c in '<>:"/\\|?*':
        name = name.replace(c, "_")
    return unquote(name.strip()) or "download"


def collect_download_urls_from_paragraphs(
    paragraphs_html: list[str],
) -> list[tuple[str, str]]:
    """Parse paragraph HTML; return ``(fetch_url, local_filename)`` for each external link."""
    found: list[tuple[str, str]] = []
    for fragment in paragraphs_html:
        if not isinstance(fragment, str) or not fragment.strip():
            continue
        soup = BeautifulSoup(fragment, "html.parser")
        for a in soup.select("a.reference.external[href]"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            label = a.get_text(strip=True)
            fname = (
                _safe_filename(label)
                if label
                else _safe_filename(Path(urlparse(href).path).name)
            )
            fetch = github_blob_url_to_raw(href)
            found.append((fetch, fname))
    return found


def collect_unique_assets_from_crawled_json(
    json_path: Path,
) -> list[tuple[str, str]]:
    """Load crawl JSON and merge links; same URL keeps the first suggested filename."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    by_url: dict[str, str] = {}
    order: list[str] = []
    for entry in data:
        paras = list(entry.get("paragraphs_html") or [])
        for fetch_url, fname in collect_download_urls_from_paragraphs(paras):
            if fetch_url not in by_url:
                by_url[fetch_url] = fname
                order.append(fetch_url)
    return [(u, by_url[u]) for u in order]


def download_assets_to_example_code(
    json_path: Path,
    example_code_dir: Path,
    *,
    client: httpx.Client | None = None,
) -> list[Path]:
    """Download all unique linked files into ``example_code_dir`` (creates the folder).

    Returns paths of files written.
    """
    example_code_dir.mkdir(parents=True, exist_ok=True)
    assets = collect_unique_assets_from_crawled_json(json_path)
    written: list[Path] = []

    own_client = client is None
    http = client or httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=httpx.Timeout(REQUEST_TIMEOUT_S),
        follow_redirects=True,
    )
    try:
        for fetch_url, fname in assets:
            dest = example_code_dir / fname
            logger.info("GET %s -> %s", fetch_url, dest)
            r = http.get(fetch_url)
            r.raise_for_status()
            dest.write_bytes(r.content)
            written.append(dest)
    finally:
        if own_client:
            http.close()

    return written


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    repo_root = Path(__file__).resolve().parent.parent
    json_path = repo_root / "crawled_examples.json"
    out_dir = repo_root / "ExampleCode"
    paths = download_assets_to_example_code(json_path, out_dir)
    for p in paths:
        logger.info("Wrote %s", p)


if __name__ == "__main__":
    main()
