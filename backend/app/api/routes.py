from __future__ import annotations

import json
import time
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_local_auth
from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.scan import Scan
from app.schemas.candidate import CandidateOut, PatchResponse, ShadowRunResponse
from app.schemas.metrics import MetricsResponse
from app.schemas.scan import ScanRequest, ScanResponse, StatusResponse
from app.services.git_service import apply_patch_in_branch, revert_branch
from app.workers.queue import enqueue_job

router = APIRouter(prefix="/api", dependencies=[Depends(require_local_auth)])


@router.post("/scan", response_model=ScanResponse)
def start_scan(payload: ScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    target = Path(payload.path).resolve()
    if not target.exists():
        raise HTTPException(status_code=400, detail="Path not found")

    scan = Scan(target_path=str(target), status="queued", progress=0, logs="")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    enqueue_job("scan", {"scan_id": scan.id, "target_path": str(target)}, scan_id=scan.id)
    return ScanResponse(scan_id=scan.id, status=scan.status)


@router.get("/status/{scan_id}", response_model=StatusResponse)
def get_status(scan_id: int, db: Session = Depends(get_db)) -> StatusResponse:
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return StatusResponse(scan_id=scan.id, status=scan.status, progress=scan.progress, logs=scan.logs)


@router.get("/results/{scan_id}", response_model=list[CandidateOut])
def get_results(scan_id: int, db: Session = Depends(get_db)) -> list[CandidateOut]:
    rows = db.query(Candidate).filter(Candidate.scan_id == scan_id).order_by(Candidate.id.asc()).all()
    return [CandidateOut.model_validate(row) for row in rows]


@router.get("/patch/{scan_id}/{candidate_id}", response_model=PatchResponse)
def get_patch(scan_id: int, candidate_id: int, db: Session = Depends(get_db)) -> PatchResponse:
    candidate = (
        db.query(Candidate)
        .filter(Candidate.scan_id == scan_id, Candidate.id == candidate_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return PatchResponse(
        candidate_id=candidate.id,
        diff=candidate.patch_diff,
        explanation=candidate.patch_explanation,
        risk_level=candidate.risk_level,
        tests_to_add=candidate.tests_to_add,
    )


@router.post("/apply/{scan_id}/{candidate_id}")
def apply_patch(
    scan_id: int,
    candidate_id: int,
    safety_flag: bool = False,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    candidate = (
        db.query(Candidate)
        .filter(Candidate.scan_id == scan_id, Candidate.id == candidate_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    if not candidate.patch_diff:
        raise HTTPException(status_code=400, detail="No patch generated")
    if not safety_flag:
        raise HTTPException(status_code=400, detail="Set safety_flag=true to apply patch")

    branch = apply_patch_in_branch(str(Path(__file__).resolve().parents[3]), scan_id, candidate_id, candidate.patch_diff)
    return {"status": "applied", "branch": branch}


@router.post("/revert/{scan_id}/{candidate_id}")
def revert_patch(scan_id: int, candidate_id: int) -> dict[str, str]:
    branch = f"ai-prune/{scan_id}/{candidate_id}"
    revert_branch(str(Path(__file__).resolve().parents[3]), branch)
    return {"status": "reverted", "branch": branch}


@router.post("/shadow-run/{scan_id}/{candidate_id}", response_model=ShadowRunResponse)
def shadow_run(scan_id: int, candidate_id: int, db: Session = Depends(get_db)) -> ShadowRunResponse:
    candidate = (
        db.query(Candidate)
        .filter(Candidate.scan_id == scan_id, Candidate.id == candidate_id)
        .first()
    )
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job_id = enqueue_job("shadow", {"candidate_id": candidate.id}, scan_id=scan_id, candidate_id=candidate.id)

    for _ in range(50):
        job = db.get(Job, job_id)
        if job and job.status == "completed":
            data = json.loads(job.result or "{}")
            return ShadowRunResponse(**data)
        db.expire_all()
        time.sleep(0.1)

    raise HTTPException(status_code=504, detail="Shadow run timed out")


@router.get("/metrics", response_model=MetricsResponse)
def metrics(db: Session = Depends(get_db)) -> MetricsResponse:
    total_scans = db.query(func.count(Scan.id)).scalar() or 0
    total_candidates = db.query(func.count(Candidate.id)).scalar() or 0
    calls_saved = db.query(func.coalesce(func.sum(Candidate.estimated_api_calls_saved), 0)).scalar() or 0
    avg_score = db.query(func.coalesce(func.avg(Candidate.rule_solvability_score), 0.0)).scalar() or 0.0
    avg_latency = db.query(func.coalesce(func.avg(Candidate.latency_improvement_ms), 0.0)).scalar() or 0.0

    return MetricsResponse(
        total_scans=int(total_scans),
        total_candidates=int(total_candidates),
        estimated_api_calls_saved=int(calls_saved),
        avg_rule_solvability_score=float(avg_score),
        avg_latency_improvement_ms=float(avg_latency),
    )
