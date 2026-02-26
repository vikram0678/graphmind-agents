from datetime import datetime, timezone
from app.agents.state import AgentState
from app.redis_client import get_workspace
from app.logger import get_logger
from app.llm import get_llm

log = get_logger()


def writing_agent(state: AgentState) -> AgentState:
    """
    WritingAgent:
    - Reads research findings from Redis workspace
    - Uses LLM to draft a comparison summary
    - Logs every action
    """
    task_id = state["task_id"]

    log.info({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "agent_name": "WritingAgent",
        "action_details": "Starting to draft comparison summary",
    })

    # ── Read from Redis workspace ──────────────────
    workspace = get_workspace(task_id=task_id)
    if workspace:
        research_findings = workspace.get("research_findings", "")
        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "WritingAgent",
            "action_details": "Successfully read research findings from Redis workspace",
        })
    else:
        research_findings = state.get("research_findings", "")
        log.warning({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "WritingAgent",
            "action_details": "Redis workspace empty, using state findings as fallback",
        })

    # ── Generate summary with LLM ──────────────────
    log.info({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "agent_name": "WritingAgent",
        "action_details": "Drafting comparison summary using LLM",
    })

    llm = get_llm()

    prompt = f"""You are a technical writer. Based on the research findings below,
write a clear and concise comparison summary of LangGraph vs CrewAI for a technical audience.

Research Findings:
{research_findings}

Write a structured comparison covering:
1. Core Architecture
2. Key Strengths
3. Best Use Cases
4. When to choose each framework

Keep it concise, technical, and actionable."""

    response = llm.invoke(prompt)
    draft = response.content if hasattr(response, "content") else str(response)

    log.info({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "agent_name": "WritingAgent",
        "action_details": "Drafting comparison summary complete. Awaiting human approval.",
    })

    # ── Update agent logs ──────────────────────────
    new_logs = state.get("agent_logs", []) + [{
        "agent": "WritingAgent",
        "action": "Drafting comparison summary",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }]

    return {
        **state,
        "draft_summary": draft,
        "agent_logs": new_logs,
        "status": "AWAITING_APPROVAL",
    }