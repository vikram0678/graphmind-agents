from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis as redis_client
import logging

from app.config import get_settings
from app.database import get_db, engine, Base
from app.models import Task  # noqa: F401
from app.routers import tasks as tasks_router
from app.routers import websockets as ws_router

settings = get_settings()

app = FastAPI(
    title="GraphMind Agents",
    description="Multi-agent AI orchestration framework built on LangGraph",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("uvicorn")

@app.on_event("startup")
async def startup_event():
    Base.metadata.create_all(bind=engine)
    logger.info("\n" + "="*55)
    logger.info("🚀  GraphMind Agents is LIVE!")
    logger.info("="*55)
    logger.info("📖  Swagger UI  →  http://localhost:8000/docs")
    logger.info("❤️   Health      →  http://localhost:8000/health")
    logger.info("🔌  WebSocket   →  ws://localhost:8000/ws/tasks/{task_id}")
    logger.info("="*55)
# ── Health Check ─────
@app.get("/health", tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    health = {
        "status": "healthy",
        "api": "ok",
        "database": "unknown",
        "redis": "unknown",
    }

    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        health["database"] = "ok"
    except Exception as e:
        health["database"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Check Redis
    try:
        r = redis_client.from_url(settings.redis_url)
        r.ping()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


# ── Root ───────
@app.get("/", tags=["Root"])
def root():
    return {
        "project": "graphmind-agents",
        "description": "Multi-agent AI orchestration framework built on LangGraph",
        "docs": "/docs",
        "health": "/health",
    }

# ── Routers ────────
app.include_router(tasks_router.router)
app.include_router(ws_router.router)