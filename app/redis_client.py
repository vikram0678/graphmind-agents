import json
import redis
from app.config import get_settings
from datetime import datetime, timezone

settings = get_settings()

# Redis connection pool
_redis_client = None


def get_redis() -> redis.Redis:
    """Get Redis client (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis_client


# ── Workspace helpers (task:<task_id>:workspace) ──

def set_workspace(task_id: str, data: dict, ttl: int = 3600):
    """Write agent findings to Redis workspace."""
    r = get_redis()
    key = f"task:{task_id}:workspace"
    r.set(key, json.dumps(data), ex=ttl)


def get_workspace(task_id: str) -> dict | None:
    """Read agent findings from Redis workspace."""
    r = get_redis()
    key = f"task:{task_id}:workspace"
    value = r.get(key)
    if value:
        return json.loads(value)
    return None


def delete_workspace(task_id: str):
    """Clean up workspace after task completes."""
    r = get_redis()
    key = f"task:{task_id}:workspace"
    r.delete(key)


# ── Approval signal helpers ───────────────────────

def set_approval(task_id: str, approved: bool, feedback: str = ""):
    """Store human approval decision."""
    r = get_redis()
    key = f"task:{task_id}:approval"
    r.set(key, json.dumps({
        "approved": approved,
        "feedback": feedback,
    }), ex=3600)


def get_approval(task_id: str) -> dict | None:
    """Get human approval decision."""
    r = get_redis()
    key = f"task:{task_id}:approval"
    value = r.get(key)
    if value:
        return json.loads(value)
    return None