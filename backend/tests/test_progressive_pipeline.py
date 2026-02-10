from pathlib import Path

from app.engine.intent_inference import infer_output_contract
from app.engine.refactor_planner import CandidateContext, ProgressiveCertaintyPlanner
from app.engine.pattern_registry.ast_utils import detect_language


def test_progressive_pipeline_exact_match_yes_no() -> None:
    root = Path(__file__).resolve().parents[2]
    file_path = root / "samples" / "python_yes_no" / "main.py"
    snippet = """resp = client.chat.completions.create(
    model=\"gpt-4o-mini\",
    messages=[{\"role\": \"user\", \"content\": prompt}],
)"""
    prompt = "Respond with ONLY YES or NO"
    language = detect_language(file_path=str(file_path))
    output_contract = infer_output_contract(prompt, snippet)

    candidate = CandidateContext(
        file_path=str(file_path),
        snippet=snippet,
        prompt=prompt,
        intent="yes_no_classification",
        language=language,
        output_contract=output_contract,
        context=prompt,
    )

    planner = ProgressiveCertaintyPlanner()
    plan = planner.plan(candidate)

    assert plan.can_apply is True
    assert plan.stage in {"exact-match", "similarity-normalized"}
    assert "deterministic" in plan.explanation.lower()
