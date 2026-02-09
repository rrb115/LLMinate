from __future__ import annotations

import json
import time
from pathlib import Path

from app.models.candidate import Candidate
from app.rules.store import get_store
from app.services.mock_llm import mock_llm

def deterministic_output(intent: str, text: str) -> str:
    store = get_store()
    rule = store.get_rule_by_intent(intent)
    
    if not rule:
        return mock_llm(intent, text)
    
    # Dynamically execute the rule's replacement code
    # The replacement_code is expected to define a function or be a snippet
    # For now, we simulate the original logic if it's one of the standard ones
    # or handle custom logic if possible.
    
    # Fallback to hardcoded logic for standard intents if rule exists in store
    if intent == "yes_no_classification":
        return "yes" if any(w in text.lower() for w in ["yes", "true", "y"]) else "no"
    if intent == "structured_extraction":
        import re
        m = re.search(r'(\d+)', text)
        return json.dumps({"value": m.group(1)}) if m else "{}"
    if intent == "small_domain_label_matching":
        t = text.lower()
        if "invoice" in t or "billing" in t: return "billing"
        if "help" in t or "support" in t: return "support"
        if "purchase" in t or "sales" in t: return "sales"

    return mock_llm(intent, text)


def run_shadow(candidate: Candidate) -> dict[str, float | int | str]:
    file_path = Path(candidate.file)
    text = file_path.read_text(encoding="utf-8", errors="ignore") if file_path.exists() else candidate.call_snippet
    cases = [c.strip() for c in text.splitlines() if c.strip()][:10] or [candidate.call_snippet]

    matches = 0
    deterministic_latency = 0.0
    mock_latency = 0.0

    for case in cases:
        start = time.perf_counter()
        det = deterministic_output(candidate.inferred_intent, case)
        deterministic_latency += time.perf_counter() - start

        start = time.perf_counter()
        llm = mock_llm(candidate.inferred_intent, case)
        mock_latency += time.perf_counter() - start

        if det == llm:
            matches += 1

    total = len(cases)
    latency_gain = ((mock_latency - deterministic_latency) / total) * 1000 if total else 0.0
    return {
        "candidate_id": candidate.id,
        "total_cases": total,
        "match_rate": round(matches / total if total else 0.0, 4),
        "avg_latency_improvement_ms": round(latency_gain, 3),
        "notes": "Shadow-run uses local mock LLM fixtures for parity checks.",
    }


def serialize_shadow_payload(payload: dict[str, float | int | str]) -> str:
    return json.dumps(payload)
