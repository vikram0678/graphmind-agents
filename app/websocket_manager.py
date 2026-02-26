import json
from typing import Dict, List
from fastapi import WebSocket


class WebSocketManager:
    """
    Manages active WebSocket connections per task.
    Broadcasts status updates to all connected clients.
    """

    def __init__(self):
        # task_id -> list of connected websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.active_connections:
            self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]

    async def broadcast(self, task_id: str, status: str):
        """Send status update to all clients watching this task."""
        if task_id not in self.active_connections:
            return

        message = json.dumps({
            "task_id": task_id,
            "status": status,
        })

        dead_connections = []
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_text(message)
            except Exception:
                dead_connections.append(websocket)

        # Clean up dead connections
        for ws in dead_connections:
            self.disconnect(task_id, ws)


# Global singleton
ws_manager = WebSocketManager()