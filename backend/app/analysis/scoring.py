from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ScoreResult:
    score: float
    risk_level: str
    estimated_api_calls_saved: int
    latency_improvement_ms: int
    fallback_behavior: str
    explanation: str


def score_solvability(intent: str, prompt: str) -> ScoreResult:
    prompt_l = prompt.lower()
    score = 0.25
    explanation = "Prompt is open-ended and likely requires model generalization."

    if intent == "yes_no_classification":
        score = 0.93
        explanation = "Binary constrained output with explicit YES/NO instructions is highly deterministic."
    elif intent == "structured_extraction":
        score = 0.86
        explanation = "Extraction against predictable fields can be replaced by regex and parsing rules."
    elif intent == "small_domain_label_matching":
        score = 0.72
        explanation = "Small-domain matching is replaceable with curated synonym tables and fuzzy matching."
    elif intent == "long_form_summarization":
        score = 0.18
        explanation = "Long-form summarization remains low-determinism and should stay model-backed."

    if "json" in prompt_l:
        score += 0.04
    if "only" in prompt_l and ("yes" in prompt_l or "enum" in prompt_l):
        score += 0.03

    score = max(0.0, min(0.99, score))
    risk = "low" if score >= 0.8 else "medium" if score >= 0.55 else "high"
    calls_saved = int(200 * score)
    latency = int(450 * score)
    fallback = (
        "If deterministic rule fails validation, fall back to original AI call path."
        if score >= 0.55
        else "Keep AI call as primary path; no automatic replacement suggested."
    )
    return ScoreResult(
        score=score,
        risk_level=risk,
        estimated_api_calls_saved=calls_saved,
        latency_improvement_ms=latency,
        fallback_behavior=fallback,
        explanation=explanation,
    )
