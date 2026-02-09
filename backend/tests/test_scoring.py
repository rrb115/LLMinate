from app.analysis.scoring import score_solvability


def test_yes_no_scoring_high() -> None:
    result = score_solvability("yes_no_classification", "Respond with ONLY YES or NO")
    assert result.score >= 0.9
    assert result.risk_level == "low"


def test_summarization_scoring_low() -> None:
    result = score_solvability("long_form_summarization", "Summarize this essay")
    assert result.score < 0.3
    assert result.risk_level == "high"
