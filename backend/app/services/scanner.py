from __future__ import annotations

from pathlib import Path
from sqlalchemy.orm import Session

from app.analysis.detector import scan_for_ai_calls
from app.analysis.intent import infer_intent
from app.analysis.scoring import score_solvability
from app.models.candidate import Candidate
from app.models.scan import Scan
from app.refactor.planner import build_patch


def append_log(scan: Scan, message: str) -> None:
    scan.logs = (scan.logs or "") + f"\n{message}"


def run_scan(db: Session, scan_id: int, target_path: str) -> None:
    scan = db.get(Scan, scan_id)
    if not scan:
        return

    scan.status = "running"
    scan.progress = 5
    append_log(scan, "Scan started")
    db.commit()

    rules_path = str(Path(__file__).resolve().parents[2] / "semgrep_rules" / "ai_calls.yml")
    hits = scan_for_ai_calls(target_path, rules_path)

    scan.progress = 50
    append_log(scan, f"Detected {len(hits)} potential AI calls")
    db.commit()

    for hit in hits:
        intent, confidence = infer_intent(hit.prompt, hit.snippet)
        score = score_solvability(intent, hit.prompt)
        patch_diff, patch_exp, tests_to_add = build_patch(
            hit.file, hit.line_start, hit.line_end, intent
        )

        candidate = Candidate(
            scan_id=scan.id,
            file=hit.file,
            line_start=hit.line_start,
            line_end=hit.line_end,
            call_snippet=hit.snippet,
            provider=hit.provider,
            inferred_intent=intent,
            rule_solvability_score=score.score,
            confidence=confidence,
            explanation=score.explanation,
            risk_level=score.risk_level,
            estimated_api_calls_saved=score.estimated_api_calls_saved,
            latency_improvement_ms=score.latency_improvement_ms,
            fallback_behavior=score.fallback_behavior,
            patch_diff=patch_diff,
            patch_explanation=patch_exp,
            tests_to_add=tests_to_add,
            auto_refactor_safe=score.score >= 0.8,
        )
        db.add(candidate)

    scan.progress = 100
    scan.status = "completed"
    append_log(scan, "Scan completed")
    db.commit()
