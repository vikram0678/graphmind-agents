from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket_manager import ws_manager
from app.database import SessionLocal
from app import crud
import asyncio
import json

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/tasks/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    """
    WebSocket endpoint for real-time task status updates.
    Streams status changes as they happen.

    Message format:
    {"task_id": "<uuid>", "status": "<status>"}
    """
    await ws_manager.connect(task_id=task_id, websocket=websocket)

    try:
        # Send current status immediately on connect
        db = SessionLocal()
        task = crud.get_task(db=db, task_id=task_id)
        db.close()

        if task:
            await websocket.send_text(json.dumps({
                "task_id": task_id,
                "status": task.status,
            }))

        # Keep connection alive — wait for client disconnect
        while True:
            try:
                # Wait for any client message (ping/pong)
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                # Send keepalive ping
                await websocket.send_text(json.dumps({
                    "task_id": task_id,
                    "status": "ping",
                }))

    except WebSocketDisconnect:
        ws_manager.disconnect(task_id=task_id, websocket=websocket)
    except Exception:
        ws_manager.disconnect(task_id=task_id, websocket=websocket)