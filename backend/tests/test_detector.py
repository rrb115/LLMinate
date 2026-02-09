from pathlib import Path

from app.analysis.detector import scan_for_ai_calls


def test_detector_finds_sample_calls() -> None:
    root = Path(__file__).resolve().parents[2]
    hits = scan_for_ai_calls(str(root / "samples"), str(root / "backend" / "semgrep_rules" / "ai_calls.yml"))
    files = {Path(h.file).name for h in hits}
    assert "main.py" in files or "main.ts" in files
    assert len(hits) >= 4
