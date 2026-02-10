from __future__ import annotations

import json
from difflib import unified_diff
from pathlib import Path

from app.engine.intent_inference import infer_output_contract
from app.engine.llm_orchestrator import LLMOrchestrator
from app.engine.pattern_registry.ast_utils import detect_language
from app.engine.refactor_planner import CandidateContext, ProgressiveCertaintyPlanner
from app.rules.store import get_store


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

    language = detect_language(file_path=str(p))
    output_contract = infer_output_contract(context, snippet)
    candidate = CandidateContext(
        file_path=str(p),
        snippet=snippet or "",
        prompt=context,
        intent=intent,
        language=language,
        output_contract=output_contract,
        context=context,
    )

    orchestrator = LLMOrchestrator(api_key=api_key, provider=api_provider)
    planner = ProgressiveCertaintyPlanner(llm_orchestrator=orchestrator)
    plan = planner.plan(candidate)

    if not plan.can_apply:
        # Legacy deterministic fallback for python intent-based rules
        store = get_store()
        legacy_rule = store.get_rule_by_intent(intent) if language == "python" else None
        if legacy_rule:
            replacement = legacy_rule.replacement_code
            tests = legacy_rule.test_case or "Add parity tests."
            explanation = "Deterministic legacy rule applied (intent-based)."
        else:
            return "", plan.explanation, plan.tests_to_add
    else:
        replacement = plan.replacement_code
        tests = plan.tests_to_add
        explanation = plan.explanation

    updated = original[:]

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
    if plan.can_apply:
        decision_trace = plan.decision_trace.to_dict()
        explanation = f"{explanation} Decision trace: {json.dumps(decision_trace)}"
    return diff, explanation, tests

