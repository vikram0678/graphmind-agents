from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
import uuid


# ── Request Schemas ──────────────────────────────
class CreateTaskRequest(BaseModel):
    prompt: str


class ApproveTaskRequest(BaseModel):
    approved: bool
    feedback: Optional[str] = None


# ── Response Schemas ─────────────────────────────
class CreateTaskResponse(BaseModel):
    task_id: str
    status: str


class TaskResponse(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    result: Optional[str] = None
    agent_logs: Optional[Any] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApproveTaskResponse(BaseModel):
    task_id: str
    status: str