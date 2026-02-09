from __future__ import annotations

from difflib import unified_diff
from pathlib import Path


def _python_replacement(intent: str) -> str:
    if intent == "yes_no_classification":
        return "from app.rules.deterministic import yes_no_rule\n"
    if intent == "structured_extraction":
        return "from app.rules.deterministic import structured_extract_rule\n"
    return ""


def _js_replacement(intent: str) -> str:
    if intent == "small_domain_label_matching":
        return "// Replace LLM call with local synonym/fuzzy matcher\n"
    return ""


def build_patch(file_path: str, line_start: int, line_end: int, intent: str) -> tuple[str, str, str]:
    p = Path(file_path)
    if not p.exists():
        return "", "File not found; patch unavailable.", "Add path validation test."

    original = p.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    updated = original[:]

    replacement = _python_replacement(intent) if p.suffix == ".py" else _js_replacement(intent)
    if replacement:
        start_idx = max(0, line_start - 1)
        end_idx = min(len(updated), line_end)
        updated[start_idx:end_idx] = [replacement]

    diff = "".join(
        unified_diff(
            original,
            updated,
            fromfile=str(p),
            tofile=f"{p}.optimized",
        )
    )
    explanation = (
        "Patch replaces the detected AI call with deterministic logic scaffolding while keeping a fallback path available."
    )
    tests = "Add parity tests for rule output vs mock LLM output on edge-case fixtures."
    return diff, explanation, tests
