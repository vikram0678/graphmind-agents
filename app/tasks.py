from app.celery_app import celery_app
import time
from app.database import SessionLocal
from app import crud


@celery_app.task(name="app.tasks.run_agent_workflow", bind=True, max_retries=3)
def run_agent_workflow(self, task_id: str, prompt: str):
    """
    Main Celery task — orchestrates the LangGraph agent workflow.
    Full agent logic will be wired in Sub-Problem 3.
    For now: updates status to RUNNING then AWAITING_APPROVAL.
    """
    db = SessionLocal()
    try:
        # Update status to RUNNING
        crud.update_task_status(db=db, task_id=task_id, status="RUNNING")

        # ── Sub-Problem 3 will replace this block ──
        # Placeholder: simulate work
        time.sleep(2)
        crud.update_task_status(db=db, task_id=task_id, status="AWAITING_APPROVAL")
        # ───────────────────────────────────────────

    except Exception as exc:
        crud.update_task_status(db=db, task_id=task_id, status="FAILED")
        raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()