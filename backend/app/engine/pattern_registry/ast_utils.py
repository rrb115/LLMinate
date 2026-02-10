from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path

try:
    from tree_sitter_language_pack import get_parser
except Exception:  # pragma: no cover
    get_parser = None

logger = logging.getLogger(__name__)

IDENTIFIER_TYPES = {
    "identifier",
    "property_identifier",
    "field_identifier",
    "variable_name",
    "type_identifier",
}
LITERAL_TYPES = {
    "string",
    "string_literal",
    "number",
    "integer",
    "float",
    "true",
    "false",
    "null",
}
CONTROL_FLOW_TYPES = {
    "if_statement",
    "if_expression",
    "conditional_expression",
    "for_statement",
    "while_statement",
    "do_statement",
    "switch_statement",
    "case_statement",
    "try_statement",
    "catch_clause",
    "with_statement",
    "match_statement",
}


@dataclass(slots=True)
class SignatureBundle:
    ast_signature: str
    control_flow_signature: str


def detect_language(file_path: str | None = None, language: str | None = None) -> str:
    if language:
        return language
    if not file_path:
        return "unknown"
    suffix = Path(file_path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".js", ".jsx"}:
        return "javascript"
    if suffix in {".ts", ".tsx"}:
        return "typescript"
    return "unknown"


def _fallback_signature(code: str) -> SignatureBundle:
    normalized = re.sub(r"\b\w+\b", "ID", code)
    normalized = re.sub(r"\d+", "NUM", normalized)
    normalized = re.sub(r"[\"\'].*?[\"\']", "STR", normalized)
    tokens = re.findall(r"[A-Za-z_]+", normalized)
    ast_signature = " ".join(tokens[:400])
    control_flow_signature = "control:" + ",".join(
        t
        for t in ["if", "for", "while", "try", "switch"]
        if t in normalized
    )
    return SignatureBundle(ast_signature=ast_signature, control_flow_signature=control_flow_signature)


def compute_signatures(code: str, language: str) -> SignatureBundle:
    if get_parser is None:
        return _fallback_signature(code)

    try:
        parser = get_parser(language)
    except Exception:
        return _fallback_signature(code)

    if parser is None:
        return _fallback_signature(code)

    tree = parser.parse(code.encode("utf-8"))
    node_types: list[str] = []
    control_counts: dict[str, int] = {k: 0 for k in CONTROL_FLOW_TYPES}

    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        node_type = node.type
        if node_type in CONTROL_FLOW_TYPES:
            control_counts[node_type] += 1
        if node_type in IDENTIFIER_TYPES:
            node_types.append("IDENT")
        elif node_type in LITERAL_TYPES:
            node_types.append("LIT")
        else:
            node_types.append(node_type)
        if len(node_types) > 500:
            break
        stack.extend(node.children)

    ast_signature = " ".join(node_types)
    control_flow_signature = ";".join(
        f"{name}:{count}" for name, count in sorted(control_counts.items()) if count > 0
    )
    return SignatureBundle(ast_signature=ast_signature, control_flow_signature=control_flow_signature)
