# GraphMind Agents 🤖

A production-ready multi-agent AI orchestration framework built on **LangGraph**, **FastAPI**, **Celery**, **PostgreSQL**, and **Redis**. Agents collaborate to research, write, and deliver results — with a human-in-the-loop approval gate and real-time WebSocket updates.

---

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                        CLIENT                              │
│           (Swagger UI / WebSocket / curl)                  │
└──────────────────┬──────────────────────────┬──────────────┘
                   │ HTTP                     │ WebSocket
                   ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI  (port 8000)                       │
│                                                             │
│  POST /api/v1/tasks          → create task                  │
│  GET  /api/v1/tasks/{id}     → get status & result          │
│  POST /api/v1/tasks/{id}/approve → human approval           │
│  WS   /ws/tasks/{id}         → live status stream           │
└──────────────────┬──────────────────────────────────────────┘
                   │ dispatches to Celery
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   Celery Worker                             │
│                                                             │
│        LangGraph StateGraph                                 │
│                                                             │
│   [research] → [write] → [await_approval] → [complete]      │
│       │              │                                      │
│  ResearchAgent   WritingAgent                               │
│  (web_search)    (LLM draft)                                │
└──────────┬──────────────────────────┬───────────────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐       ┌──────────────────────┐
│   PostgreSQL     │       │        Redis         │
│                  │       │                      │
│  tasks table     │       │  agent workspace     │
│  agent_logs JSONB│       │  approval decisions  │
│  final result    │       │  Celery broker       │
└──────────────────┘       └──────────────────────┘
                                      │
                           ┌──────────────────────┐
                           │  logs/               │
                           │  agent_activity.log  │
                           │  (JSON lines)        │
                           └──────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Agent Orchestration | LangGraph |
| Task Queue | Celery |
| Message Broker | Redis |
| Database | PostgreSQL |
| Real-time Updates | WebSocket |
| LLM Provider | Groq (llama-3.3-70b-versatile) |
| Containerization | Docker + Docker Compose |

---

## Project Structure

```
graphmind-agents/
├── app/
│   ├── agents/
│   │   ├── graph.py            # LangGraph StateGraph definition
│   │   ├── research_agent.py   # Searches web, saves to Redis
│   │   ├── writing_agent.py    # Reads Redis, drafts via LLM
│   │   ├── state.py            # AgentState TypedDict
│   │   └── tools.py            # web_search with flaky retry
│   ├── routers/
│   │   ├── tasks.py            # POST/GET task endpoints
│   │   └── websockets.py       # WS /ws/tasks/{task_id}
│   ├── celery_app.py           # Celery configuration
│   ├── config.py               # Pydantic settings
│   ├── crud.py                 # Database operations
│   ├── database.py             # SQLAlchemy engine + session
│   ├── llm.py                  # LLM provider factory
│   ├── logger.py               # Structured JSON logger
│   ├── main.py                 # FastAPI app entry point
│   ├── models.py               # SQLAlchemy Task model
│   ├── redis_client.py         # Redis workspace helpers
│   ├── schemas.py              # Pydantic request/response models
│   ├── tasks.py                # Celery task + broadcast logic
│   └── websocket_manager.py    # WebSocket connection manager
├── migrations/
│   └── init.sql                # PostgreSQL schema
├── logs/
│   └── agent_activity.log      # Auto-created on first run
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env
└── .env.example
```

---

## Quick Start

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

---

### Step 1 — Clone the repo

```bash
git clone https://github.com/vikram0678/graphmind-agents.git
cd graphmind-agents
```

---

### Step 2 — Create your `.env` file

```bash
cp .env.example .env
```

Edit `.env` and fill in your API key:

```env
# LLM Provider — groq | openai | google | ollama | anthropic | openrouter | universal
LLM_PROVIDER=groq
LLM_API_KEY=gsk_your_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=

# Database
POSTGRES_USER=graphmind
POSTGRES_PASSWORD=graphmind_pass
POSTGRES_DB=graphmind_db
DATABASE_URL=postgresql://graphmind:graphmind_pass@db:5432/graphmind_db

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# API
API_PORT=8000
```

---

### Step 3 — Get a free Groq API key

```
1. Go to  →  https://console.groq.com
2. Sign up with Google
3. Click API Keys → Create API Key
4. Copy and paste it into .env as LLM_API_KEY
```

---

### Step 4 — Start all services

```bash
docker compose up --build
```

Wait until you see all 4 services healthy:

```
✔ Container graphmind_db      Healthy
✔ Container graphmind_redis   Healthy
✔ Container graphmind_api     Healthy
✔ Container graphmind_worker  Healthy
```

---

### Step 5 — Open Swagger UI

```
http://localhost:8000/docs
```

---

## Running a Full Workflow — Step by Step

---

### 1. Open Two Things Side by Side

```
Left  →  http://localhost:8000/docs   (Swagger UI)
Right →  Browser DevTools Console     (F12 → Console tab)
```

---

### 2. Set Up WebSocket Listener in Console First

Paste this in the browser console and press Enter:

```javascript
function connectAndWatch(taskId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`)
    ws.onopen = () => console.log("✅ Connected!")
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (data.status !== 'ping') {
            console.log("📡 Status:", data.status)
        }
    }
    ws.onclose = () => console.log("❌ Disconnected")
}
console.log("✅ Function ready!")
```

You should see: `✅ Function ready!`

---

### 3. Create a Task in Swagger

Go to `POST /api/v1/tasks` → Try it out → paste prompt → Execute:

```json
{
  "prompt": "Research the key features of LangGraph and CrewAI. Write a short comparison summary for a technical audience."
}
```

Response:

```json
{
  "task_id": "46b728c3-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "PENDING"
}
```

**Copy the `task_id` immediately.**

---

### 4. Connect WebSocket — Do This Within 3 Seconds!

Paste in console with your real task_id:

```javascript
connectAndWatch("46b728c3-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
```

Watch the live updates:

```
✅ Connected!
📡 Status: RUNNING
📡 Status: AWAITING_APPROVAL   ← approve now!
```

---

### 5. Approve the Task in Swagger

Go to `POST /api/v1/tasks/{task_id}/approve` → Try it out → Execute:

```json
{
  "approved": true,
  "feedback": "Looks good to proceed."
}
```

Response:

```json
{
  "task_id": "46b728c3-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "status": "RESUMED"
}
```

---

### 6. Watch Console — Final Status

```
📡 Status: COMPLETED ✅
```

---

### 7. View the Final Result

Go to `GET /api/v1/tasks/{task_id}` → Execute:

```json
{
  "id": "46b728c3-...",
  "status": "COMPLETED",
  "result": "**Comparison Summary: LangGraph vs CrewAI**...",
  "agent_logs": [
    {
      "agent": "ResearchAgent",
      "action": "Searching for LangGraph features",
      "timestamp": "2026-02-26T12:25:19Z"
    },
    {
      "agent": "WritingAgent",
      "action": "Drafting comparison summary",
      "timestamp": "2026-02-26T12:25:22Z"
    }
  ]
}
```

---

## Workflow Timeline

```
0 sec   → Create task in Swagger → copy task_id
0 sec   → Run connectAndWatch("task_id") in console
~2 sec  → 📡 Status: RUNNING
~15 sec → 📡 Status: AWAITING_APPROVAL
~15 sec → Approve in Swagger
~17 sec → 📡 Status: COMPLETED ✅
```

---

## Task Status Flow

```
PENDING
   │
   ▼  Celery picks up the task
RUNNING
   │
   ▼  ResearchAgent + WritingAgent finish
AWAITING_APPROVAL
   │
   ├── approved: true  ──▶  COMPLETED
   │
   └── approved: false ──▶  FAILED
       (or auto-timeout after 5 minutes)
```

---

## API Reference

### `POST /api/v1/tasks`
Create a new task. Returns instantly with a task ID.

**Request:**
```json
{ "prompt": "your prompt here" }
```

**Response `202`:**
```json
{ "task_id": "uuid", "status": "PENDING" }
```

---

### `GET /api/v1/tasks/{task_id}`
Get full details of a task.

**Response `200`:**
```json
{
  "id": "uuid",
  "prompt": "...",
  "status": "COMPLETED",
  "result": "final summary text...",
  "agent_logs": [...],
  "created_at": "2026-02-26T12:25:16Z",
  "updated_at": "2026-02-26T12:25:22Z"
}
```

---

### `POST /api/v1/tasks/{task_id}/approve`
Resume a paused workflow.

**Request:**
```json
{ "approved": true, "feedback": "Looks good!" }
```

**Response `200`:**
```json
{ "task_id": "uuid", "status": "RESUMED" }
```

---

### `WS /ws/tasks/{task_id}`
Real-time status stream via WebSocket.

**Browser Console:**
```javascript
function connectAndWatch(taskId) {
    const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`)
    ws.onopen = () => console.log("✅ Connected!")
    ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (data.status !== 'ping') {
            console.log("📡 Status:", data.status)
        }
    }
    ws.onclose = () => console.log("❌ Disconnected")
}
connectAndWatch("your-task-id-here")
```

**Messages you'll receive:**
```
📡 Status: RUNNING
📡 Status: AWAITING_APPROVAL
📡 Status: COMPLETED
```

---

## Observability

### Check Logs

```bash
# Linux / Mac
docker exec graphmind_api cat /app/logs/agent_activity.log

# Windows Git Bash
docker exec graphmind_api //bin/cat //app/logs/agent_activity.log
```

Sample output:
```json
{"timestamp": "2026-02-26T16:14:26Z", "task_id": "...", "agent_name": "ResearchAgent", "action_details": "Starting research", "level": "INFO"}
{"timestamp": "2026-02-26T16:14:33Z", "task_id": "...", "agent_name": "WritingAgent", "action_details": "Drafting complete. Awaiting approval.", "level": "INFO"}
{"timestamp": "2026-02-26T16:15:27Z", "task_id": "...", "agent_name": "Orchestrator", "action_details": "Workflow COMPLETED successfully.", "level": "INFO"}
```

---

### Check Redis Workspace

```bash
# List all task keys
docker exec graphmind_redis redis-cli keys "task:*"

# Read agent findings
docker exec graphmind_redis redis-cli get "task:YOUR_TASK_ID:workspace"
```

---

### Check Database

```bash
docker exec graphmind_db psql -U graphmind -d graphmind_db \
  -c "SELECT id, status, agent_logs FROM tasks ORDER BY created_at DESC LIMIT 5;"
```

---

### Health Check

```bash
curl http://localhost:8000/health
```

```json
{
  "status": "healthy",
  "api": "ok",
  "database": "ok",
  "redis": "ok"
}
```

---

## Flaky Tool Retry Demo

To verify the retry mechanism works:

**Create this task:**
```json
{ "prompt": "__FLAKY_TEST__" }
```

**Check logs:**
```bash
docker exec graphmind_api //bin/grep -i "attempt\|retry\|flaky" //app/logs/agent_activity.log
```

**Expected output:**
```
"action_details": "Tool failed on attempt 1: Simulated tool failure"
"action_details": "Retrying web search... (attempt 2)"
"action_details": "Searching for '__FLAKY_TEST__' (attempt 2)"
```

---

## Supported LLM Providers

| Provider | `LLM_PROVIDER` | Example Model |
|---|---|---|
| Groq ⭐ recommended | `groq` | `llama-3.3-70b-versatile` |
| OpenAI | `openai` | `gpt-4o` |
| Google Gemini | `google` | `gemini-2.0-flash` |
| Anthropic Claude | `anthropic` | `claude-3-5-sonnet-20241022` |
| OpenRouter (600+ models) | `openrouter` | `meta-llama/llama-3.3-70b-instruct:free` |
| Ollama local | `ollama` | `llama3.2` |
| Any OpenAI-compatible API | `universal` | set `LLM_BASE_URL` in `.env` |

---