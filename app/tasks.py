import time
import asyncio
from datetime import datetime, timezone
from app.celery_app import celery_app
from app.database import SessionLocal
from app import crud
from app.redis_client import get_approval, delete_workspace
from app.agents.graph import build_graph
from app.logger import get_logger

log = get_logger()

def broadcast_status(task_id: str, status: str):
    """
    Broadcast status update to all WebSocket clients.
    Runs async broadcast from sync Celery worker.
    """
    try:
        from app.websocket_manager import ws_manager
        loop = asyncio.new_event_loop()
        loop.run_until_complete(ws_manager.broadcast(task_id, status))
        loop.close()
    except Exception as e:
        log.warning({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "action_details": f"WebSocket broadcast failed: {str(e)}",
        })


@celery_app.task(
    name="app.tasks.run_agent_workflow", 
    bind=True, 
    max_retries=3
)
def run_agent_workflow(self, task_id: str, prompt: str):
    """
    Main Celery task — runs the full LangGraph agent workflow.

    Flow:
    1. PENDING → RUNNING
    2. ResearchAgent gathers info → saves to Redis
    3. WritingAgent reads Redis → drafts summary
    4. Status → AWAITING_APPROVAL (pause)
    5. Poll Redis for human approval
    6. On approval → COMPLETED with result saved to DB
    """
    db = SessionLocal()
    try:
        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "action_details": f"Starting workflow for prompt: '{prompt}'",
        })
        
        # ── Step 1: Mark as RUNNING
        crud.update_task_status(db=db, task_id=task_id, status="RUNNING")

        broadcast_status(task_id, "RUNNING")

        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "action_details": "Status changed to RUNNING",
        })

        # ── Step 2: Build and run LangGraph ───────
        graph = build_graph()

        initial_state = {
            "task_id": task_id,
            "prompt": prompt,
            "research_findings": None,
            "draft_summary": None,
            "agent_logs": [],
            "status": "RUNNING",
            "result": None,
            "approved": None,
            "feedback": None,
            "error": None,
        }

        # Run graph up to AWAITING_APPROVAL
        final_state = graph.invoke(initial_state)

        # ── Step 3: Save agent logs to DB ─────────
        crud.update_task_result(
            db=db,
            task_id=task_id,
            status="AWAITING_APPROVAL",
            agent_logs=final_state.get("agent_logs", []),
        )
        broadcast_status(task_id, "AWAITING_APPROVAL")


        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "action_details": "Workflow paused. Waiting for human approval.",
        })

        # ── Step 4: Poll for human approval ───────
        max_wait = 300  # 5 minutes
        poll_interval = 3
        waited = 0

        while waited < max_wait:
            db.expire_all()
            task_row = crud.get_task(db=db, task_id=task_id)

            if task_row and task_row.status == "RESUMED":
                approval = get_approval(task_id=task_id)
                approved = approval.get("approved", False) if approval else False
                feedback = approval.get("feedback", "") if approval else ""

                log.info({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": task_id,
                    "agent_name": "Orchestrator",
                    "action_details": f"Human approval received: approved={approved}, feedback='{feedback}'",
                })

                if approved:
                    # ── Step 5: Complete the task ──
                    crud.update_task_result(
                        db=db,
                        task_id=task_id,
                        status="COMPLETED",
                        result=final_state.get("draft_summary", ""),
                        agent_logs=final_state.get("agent_logs", []),
                    )
                    broadcast_status(task_id, "COMPLETED")


                    delete_workspace(task_id=task_id)

                    log.info({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "task_id": task_id,
                        "agent_name": "Orchestrator",
                        "action_details": "Workflow COMPLETED successfully.",
                    })
                else:
                    crud.update_task_status(
                        db=db, task_id=task_id, status="FAILED"
                    )
                    broadcast_status(task_id, "FAILED")

                    log.warning({
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "task_id": task_id,
                        "agent_name": "Orchestrator",
                        "action_details": "Task rejected by human. Marked as FAILED.",
                    })
                break

            time.sleep(poll_interval)
            waited += poll_interval

        else:
            # Timeout
            crud.update_task_status(db=db, task_id=task_id, status="FAILED")
            log.error({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "agent_name": "Orchestrator",
                "action_details": "Workflow timed out waiting for approval.",
            })

    except Exception as exc:
        log.error({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "Orchestrator",
            "action_details": f"Workflow failed with error: {str(exc)}",
        })
        crud.update_task_status(db=db, task_id=task_id, status="FAILED")
        broadcast_status(task_id, "FAILED")
        raise self.retry(exc=exc, countdown=5)

    # except Exception as exc:
    #     crud.update_task_status(db=db, task_id=task_id, status="FAILED")
    #     raise self.retry(exc=exc, countdown=5)
    finally:
        db.close()