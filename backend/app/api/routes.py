import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from git import Repo
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import require_local_auth
from app.db.session import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.scan import Scan
from app.schemas.candidate import CandidateOut, PatchResponse, ShadowRunResponse
from app.schemas.metrics import MetricsResponse
from app.schemas.scan import ScanRequest, GitScanRequest, ScanResponse, StatusResponse
from app.services.git_service import apply_patch_in_branch, revert_branch
from app.refactor.planner import get_rule_code
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

    enqueue_job(
        "scan", 
        {
            "scan_id": scan.id, 
            "target_path": str(target),
            "api_key": payload.api_key,
            "api_provider": payload.api_provider
        }, 
        scan_id=scan.id
    )
    return ScanResponse(scan_id=scan.id, status=scan.status)



@router.post("/scan/upload", response_model=ScanResponse)
async def upload_scan(
    file: UploadFile = File(...), 
    api_key: str | None = Form(None),
    api_provider: str | None = Form(None),
    db: Session = Depends(get_db)
) -> ScanResponse:
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    upload_dir = Path(tempfile.gettempdir()) / "llminate_uploads"
    upload_dir.mkdir(exist_ok=True)
    
    # create a unique directory for this scan
    scan_subdir = upload_dir / f"scan_{int(time.time())}"
    scan_subdir.mkdir(exist_ok=True)
    
    zip_path = scan_subdir / file.filename

    with zip_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    extract_path = scan_subdir / "extracted"
    extract_path.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)
    except zipfile.BadZipFile:
        shutil.rmtree(scan_subdir)
        raise HTTPException(status_code=400, detail="Invalid zip file")

    # Find the root of the project (heuristic: look for the first directory if it's nested)
    # Often zips contain a root directory 'project/' then files.
    contents = list(extract_path.iterdir())
    if len(contents) == 1 and contents[0].is_dir():
        target = contents[0]
    else:
        target = extract_path

    scan = Scan(target_path=str(target.resolve()), status="queued", progress=0, logs="")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    enqueue_job(
        "scan", 
        {
            "scan_id": scan.id, 
            "target_path": str(target.resolve()),
            "api_key": api_key,
            "api_provider": api_provider
        }, 
        scan_id=scan.id
    )
    return ScanResponse(scan_id=scan.id, status=scan.status)


@router.post("/scan/git", response_model=ScanResponse)
def start_git_scan(payload: GitScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    clone_dir = Path(tempfile.gettempdir()) / "llminate_clones"
    clone_dir.mkdir(exist_ok=True)
    
    # create a unique directory for this repo
    # Extract repo name for readability if possible
    repo_name = payload.url.rstrip("/").split("/")[-1].replace(".git", "")
    target_dir = clone_dir / f"{repo_name}_{int(time.time())}"
    
    try:
        Repo.clone_from(payload.url, target_dir, depth=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Git clone failed: {str(e)}")

    scan = Scan(target_path=str(target_dir.resolve()), status="queued", progress=0, logs="")
    db.add(scan)
    db.commit()
    db.refresh(scan)

    enqueue_job(
        "scan", 
        {
            "scan_id": scan.id, 
            "target_path": str(target_dir.resolve()),
            "api_key": payload.api_key,
            "api_provider": payload.api_provider
        }, 
        scan_id=scan.id
    )
    return ScanResponse(scan_id=scan.id, status=scan.status)


@router.get("/status/{scan_id}", response_model=StatusResponse)
def get_status(scan_id: int, db: Session = Depends(get_db)) -> StatusResponse:
    scan = db.get(Scan, scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return StatusResponse(scan_id=scan.id, status=scan.status, progress=scan.progress, logs=scan.logs)


@router.get("/results/{scan_id}", response_model=dict[str, list[CandidateOut]])
def get_results(scan_id: int, db: Session = Depends(get_db)) -> dict[str, list[CandidateOut]]:
    rows = db.query(Candidate).filter(Candidate.scan_id == scan_id).order_by(Candidate.file.asc(), Candidate.line_start.asc()).all()
    grouped: dict[str, list[CandidateOut]] = {}
    for row in rows:
        c = CandidateOut.model_validate(row)
        if c.file not in grouped:
            grouped[c.file] = []
        grouped[c.file].append(c)
    return grouped


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
        rule_code=get_rule_code(candidate.inferred_intent),
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
