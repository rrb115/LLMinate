from pathlib import Path

from app.refactor.planner import build_patch


def test_patch_generation_for_yes_no() -> None:
    root = Path(__file__).resolve().parents[2]
    file_path = root / "samples" / "python_yes_no" / "main.py"
    diff, explanation, tests = build_patch(str(file_path), 8, 12, "yes_no_classification")
    assert "@@" in diff
    assert "deterministic" in explanation.lower()
    assert "tests" in tests.lower()
