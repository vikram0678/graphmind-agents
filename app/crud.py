import uuid
from sqlalchemy.orm import Session
from app.models import Task


def create_task(db: Session, prompt: str) -> Task:
    """Create a new task with PENDING status."""
    task = Task(
        prompt=prompt,
        status="PENDING",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: str) -> Task | None:
    """Get a task by ID."""
    try:
        uid = uuid.UUID(task_id)
    except ValueError:
        return None
    return db.query(Task).filter(Task.id == uid).first()


def update_task_status(db: Session, task_id: str, status: str) -> Task | None:
    """Update task status."""
    task = get_task(db, task_id)
    if not task:
        return None
    task.status = status
    db.commit()
    db.refresh(task)
    return task


def update_task_result(
    db: Session,
    task_id: str,
    status: str,
    result: str = None,
    agent_logs: list = None,
) -> Task | None:
    """Update task with final result and logs."""
    task = get_task(db, task_id)
    if not task:
        return None
    task.status = status
    if result is not None:
        task.result = result
    if agent_logs is not None:
        task.agent_logs = agent_logs
    db.commit()
    db.refresh(task)
    return task