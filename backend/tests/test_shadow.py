from pathlib import Path

from app.models.candidate import Candidate
from app.services.shadow import run_shadow


def test_shadow_run_payload_shape() -> None:
    root = Path(__file__).resolve().parents[2]
    file_path = root / "samples" / "python_yes_no" / "main.py"
    candidate = Candidate(
        id=123,
        scan_id=1,
        file=str(file_path),
        line_start=1,
        line_end=3,
        call_snippet="respond with ONLY YES or NO",
        provider="openai",
        inferred_intent="yes_no_classification",
        rule_solvability_score=0.9,
        confidence=0.9,
        explanation="",
        risk_level="low",
        estimated_api_calls_saved=1,
        latency_improvement_ms=10,
        fallback_behavior="",
        patch_diff="",
        patch_explanation="",
        tests_to_add="",
        auto_refactor_safe=True,
    )
    out = run_shadow(candidate)
    assert out["candidate_id"] == 123
    assert 0 <= out["match_rate"] <= 1
