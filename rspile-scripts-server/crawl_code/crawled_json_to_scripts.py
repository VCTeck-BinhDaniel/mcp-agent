"""Export Python ``code_blocks`` from ``crawled_examples.json`` into ``.py`` files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import urlparse


def _script_stem_from_doc_url(url: str) -> str:
    """``.../examples/pile_sections/foo.html`` → ``pile_sections_foo``."""
    path = urlparse(url).path
    marker = "/examples/"
    if marker in path:
        rel = path.split(marker, 1)[1]
    else:
        rel = path.rstrip("/").rsplit("/", 1)[-1]
    rel = rel.removesuffix(".html").strip("/")
    stem = rel.replace("/", "_")
    return stem or "example"


def _is_rspile_example_python(code: str) -> bool:
    """Heuristic: real scripts import / use RSPile; trailing blocks are usually print output."""
    t = code.lstrip()
    if not t:
        return False
    if "RSPileScripting" in t or "RSPileModeler" in t:
        return True
    first = t.splitlines()[0]
    return first.startswith(("from ", "import "))


def _safe_filename_segment(name: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]', "_", name)
    return cleaned.strip(" .") or "script"


def export_codeblocks_from_crawled_json(
    json_path: Path,
    out_dir: Path,
    *,
    write_output_txt: bool = False,
) -> list[Path]:
    """Parse ``crawled_examples.json`` and write each RSPile example script to ``out_dir``.

    Skips non-Python blocks (e.g. captured stdout after the script). Optional
    ``*_output.txt`` files when ``write_output_txt`` is True.

    Returns paths of files written (``.py`` and optionally ``.txt``).
    """
    raw = json.loads(json_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    for entry in raw:
        url = str(entry.get("url", ""))
        stem = _safe_filename_segment(_script_stem_from_doc_url(url))
        blocks: list[str] = list(entry.get("code_blocks") or [])
        py_blocks: list[str] = []
        other_blocks: list[str] = []
        for b in blocks:
            if isinstance(b, str) and _is_rspile_example_python(b):
                py_blocks.append(b)
            elif isinstance(b, str) and b.strip():
                other_blocks.append(b)

        for i, src in enumerate(py_blocks, start=1):
            suffix = "" if len(py_blocks) == 1 else f"_{i}"
            path = out_dir / f"{stem}{suffix}.py"
            path.write_text(src.rstrip() + "\n", encoding="utf-8")
            written.append(path)

        if write_output_txt and other_blocks:
            for i, text in enumerate(other_blocks, start=1):
                suffix = "" if len(other_blocks) == 1 else f"_{i}"
                path = out_dir / f"{stem}_output{suffix}.txt"
                path.write_text(text.rstrip() + "\n", encoding="utf-8")
                written.append(path)

    return written


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    json_path = repo_root / "crawled_examples.json"
    out_dir = repo_root / "rspil_scripts_python"
    paths = export_codeblocks_from_crawled_json(json_path, out_dir)
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
