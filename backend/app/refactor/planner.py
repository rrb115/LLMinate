from __future__ import annotations

from difflib import unified_diff
import inspect
from pathlib import Path

from app.rules.store import get_store
from app.analysis.agent import get_agent


def get_rule_code(intent: str) -> str:
    store = get_store()
    rule = store.get_rule_by_intent(intent)
    return rule.replacement_code if rule else ""



def build_patch(
    file_path: str, 
    line_start: int, 
    line_end: int, 
    intent: str, 
    snippet: str = "",
    api_key: str | None = None,
    api_provider: str | None = None
) -> tuple[str, str, str]:
    p = Path(file_path)
    if not p.exists():
        return "", "File not found; patch unavailable.", "Add path validation test."

    original = p.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    
    # Context for AI agent if needed
    start_ctx = max(0, line_start - 5)
    end_ctx = min(len(original), line_end + 5)
    context = "".join(original[start_ctx:end_ctx])

    store = get_store()
    
    # 1. Try to find an existing rule
    rule = store.get_rule_by_intent(intent)
    
    # 2. If no rule, try to generate one via AI Agent
    if not rule and snippet:
        # TODO: In a real system, we might want to check if the user *wants* to generate a rule first
        # For now, we auto-generate.
        agent = get_agent(api_key=api_key, provider=api_provider)
        rule = agent.generate_rule(snippet, context, intent)
        if rule:
            # Save the newly learned rule to the private store
            store.save_rule(rule)

    if not rule:
        return "", "No deterministic rule available for this pattern yet.", "Consider implementing a manual override."

    updated = original[:]
    
    # Ensure replacement code ends with newline 
    replacement = rule.replacement_code
    if not replacement.endswith("\n"):
        replacement += "\n"

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
        f"Replaced AI call with deterministic logic '{rule.id}' from {rule.language} rule store."
    )
    tests = rule.test_case or "Add parity tests for rule output."
    return diff, explanation, tests

