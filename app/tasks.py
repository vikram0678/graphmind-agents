from app.celery_app import celery_app


@celery_app.task(name="app.tasks.placeholder")
def placeholder_task(task_id: str):
    """
    Placeholder — will be replaced with full
    LangGraph agent workflow in Sub-Problem 3.
    """
    return {"task_id": task_id, "status": "placeholder"}