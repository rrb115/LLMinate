from __future__ import annotations

import json
import time
from pathlib import Path

from app.models.candidate import Candidate
from app.rules.deterministic import fuzzy_label_match, serialize_result, structured_extract_rule, yes_no_rule
from app.services.mock_llm import mock_llm


def deterministic_output(intent: str, text: str) -> str:
    if intent == "yes_no_classification":
        return yes_no_rule(text)
    if intent == "structured_extraction":
        return serialize_result(structured_extract_rule(text))
    if intent == "small_domain_label_matching":
        return fuzzy_label_match(
            text,
            labels=["billing", "support", "sales"],
            synonyms={"invoice": "billing", "help": "support", "purchase": "sales"},
        )
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
