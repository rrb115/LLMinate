from pathlib import Path

from app.models.candidate import Candidate
from app.models.scan import Scan
from app.services.scanner import run_scan


def test_scan_samples_generates_expected_candidates(db_session) -> None:
    root = Path(__file__).resolve().parents[2]
    scan = Scan(target_path=str(root / "samples"), status="queued", progress=0, logs="")
    db_session.add(scan)
    db_session.commit()
    db_session.refresh(scan)

    run_scan(db_session, scan.id, str(root / "samples"))

    candidates = db_session.query(Candidate).filter(Candidate.scan_id == scan.id).all()
    intents = {c.inferred_intent for c in candidates}

    assert "yes_no_classification" in intents
    assert "structured_extraction" in intents
    assert "small_domain_label_matching" in intents
    assert "long_form_summarization" in intents

    yes_no = next(c for c in candidates if c.inferred_intent == "yes_no_classification")
    non_replaceable = next(c for c in candidates if c.inferred_intent == "long_form_summarization")

    assert yes_no.rule_solvability_score >= 0.8
    assert non_replaceable.rule_solvability_score < 0.4
