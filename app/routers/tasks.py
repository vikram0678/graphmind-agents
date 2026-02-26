from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CreateTaskRequest,
    CreateTaskResponse,
    TaskResponse,
    ApproveTaskRequest,
    ApproveTaskResponse,
)
from app import crud
from app.redis_client import set_approval
from app.tasks import run_agent_workflow

router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])


# ── POST /api/v1/tasks ────────────────────────────
@router.post("", status_code=202, response_model=CreateTaskResponse)
def create_task(payload: CreateTaskRequest, db: Session = Depends(get_db)):
    """
    Create a new agent task.
    Immediately returns 202 with task_id.
    Queues the actual work to Celery worker.
    """
    # 1. Save to DB with PENDING status
    task = crud.create_task(db=db, prompt=payload.prompt)
    task_id = str(task.id)

    # 2. Dispatch to Celery worker (non-blocking)
    run_agent_workflow.delay(task_id, payload.prompt)

    return CreateTaskResponse(task_id=task_id, status="PENDING")


# ── GET /api/v1/tasks/{task_id} ───────────────────
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get current status and details of a task."""
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── POST /api/v1/tasks/{task_id}/approve ─────────
@router.post("/{task_id}/approve", response_model=ApproveTaskResponse)
def approve_task(
    task_id: str,
    payload: ApproveTaskRequest,
    db: Session = Depends(get_db),
):
    """
    Human-in-the-loop approval gate.
    Stores approval decision in Redis so the
    paused Celery worker can read and resume.
    """
    task = crud.get_task(db=db, task_id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "AWAITING_APPROVAL":
        raise HTTPException(
            status_code=400,
            detail=f"Task is not awaiting approval. Current status: {task.status}",
        )

    # Store approval in Redis
    set_approval(
        task_id=task_id,
        approved=payload.approved,
        feedback=payload.feedback or "",
    )

    # Update status to RESUMED
    crud.update_task_status(db=db, task_id=task_id, status="RESUMED")

    return ApproveTaskResponse(task_id=task_id, status="RESUMED")