from __future__ import annotations

import json
import threading
import time

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.models.job import Job
from app.services.scanner import run_scan
from app.services.shadow import run_shadow, serialize_shadow_payload

_running = False
_lock = threading.Lock()


def enqueue_job(kind: str, payload: dict, scan_id: int | None = None, candidate_id: int | None = None) -> int:
    with SessionLocal() as db:
        job = Job(
            kind=kind,
            payload=json.dumps(payload),
            scan_id=scan_id,
            candidate_id=candidate_id,
            status="queued",
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return int(job.id)


def _process_job(db: Session, job: Job) -> None:
    payload = json.loads(job.payload or "{}")
    job.status = "running"
    db.commit()

    if job.kind == "scan":
        run_scan(db, int(payload["scan_id"]), payload["target_path"])
        job.result = "scan_complete"
    elif job.kind == "shadow":
        candidate = db.get(Candidate, int(payload["candidate_id"]))
        if candidate:
            shadow_payload = run_shadow(candidate)
            job.result = serialize_shadow_payload(shadow_payload)

    job.status = "completed"
    db.commit()


def _loop() -> None:
    global _running
    while _running:
        with SessionLocal() as db:
            job = db.query(Job).filter(Job.status == "queued").order_by(Job.id.asc()).first()
            if job:
                _process_job(db, job)
        time.sleep(0.2)


def start_worker() -> None:
    global _running
    with _lock:
        if _running:
            return
        _running = True
        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()


def stop_worker() -> None:
    global _running
    with _lock:
        _running = False
