from __future__ import annotations

import re
from pathlib import Path

try:
    from tree_sitter_language_pack import get_parser
except Exception:  # pragma: no cover
    get_parser = None

AI_TOKEN_RE = re.compile(r"openai|anthropic|gemini|chat|generate|messages", re.IGNORECASE)


def _line_offsets(text: str) -> list[int]:
    offsets = [0]
    for line in text.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return offsets


def _extract_segment(text: str, start_row: int, end_row: int) -> str:
    lines = text.splitlines()
    return "\n".join(lines[start_row : min(end_row + 1, len(lines))])


def extract_calls(path: Path) -> list[tuple[int, int, str]]:
    if get_parser is None:
        return []

    lang = None
    if path.suffix.lower() == ".py":
        lang = "python"
    elif path.suffix.lower() in {".js", ".jsx"}:
        lang = "javascript"
    elif path.suffix.lower() in {".ts", ".tsx"}:
        lang = "typescript"
    if not lang:
        return []

    parser = get_parser(lang)
    text = path.read_text(encoding="utf-8", errors="ignore")
    tree = parser.parse(text.encode("utf-8"))

    nodes: list[tuple[int, int, str]] = []
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type in {"call", "call_expression"}:
            snippet = _extract_segment(text, node.start_point[0], node.end_point[0])
            if AI_TOKEN_RE.search(snippet):
                nodes.append((node.start_point[0] + 1, node.end_point[0] + 1, snippet[:800]))
        stack.extend(node.children)
    return nodes
