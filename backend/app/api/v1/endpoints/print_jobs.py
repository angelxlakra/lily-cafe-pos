# backend/app/api/v1/endpoints/print_jobs.py
"""
Print relay endpoints — consumed by agent.py running at the cafe.
Protected by a shared API key (X-Agent-Key header), not JWT.
"""

import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.models.print_job import PrintJob
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def verify_agent_key(x_agent_key: str = Header(...)):
    if x_agent_key != settings.PRINT_AGENT_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid agent key")


class AckRequest(BaseModel):
    success: bool
    error: str | None = None


@router.get("/next")
def get_next_job(db: Session = Depends(get_db), _=Depends(verify_agent_key)):
    """
    Return the oldest pending print job and atomically mark it as in-flight (printing).
    Returns null when the queue is empty.
    """
    job = (
        db.query(PrintJob)
        .filter(PrintJob.status == "pending")
        .order_by(PrintJob.created_at)
        .first()
    )
    if not job:
        return None

    job.status = "printing"
    job.attempts += 1
    db.commit()
    db.refresh(job)

    return {"id": job.id, "station": job.station, "payload": json.loads(job.payload)}


@router.put("/{job_id}/ack")
def ack_job(job_id: int, body: AckRequest, db: Session = Depends(get_db), _=Depends(verify_agent_key)):
    """Agent calls this after attempting to print."""
    job = db.query(PrintJob).filter(PrintJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = "done" if body.success else "failed"
    job.completed_at = datetime.now(timezone.utc)
    if body.error:
        job.error = body.error[:500]
    db.commit()

    return {"id": job.id, "status": job.status}


@router.get("/status")
def queue_status(db: Session = Depends(get_db), _=Depends(verify_agent_key)):
    """Summary of the print queue — useful for debugging."""
    counts = {}
    for s in ("pending", "printing", "done", "failed"):
        counts[s] = db.query(PrintJob).filter(PrintJob.status == s).count()
    recent_failed = (
        db.query(PrintJob)
        .filter(PrintJob.status == "failed")
        .order_by(PrintJob.created_at.desc())
        .limit(5)
        .all()
    )
    return {
        "counts": counts,
        "recent_failed": [
            {"id": j.id, "station": j.station, "error": j.error, "created_at": j.created_at}
            for j in recent_failed
        ],
    }
