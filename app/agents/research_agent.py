from datetime import datetime, timezone
from app.agents.state import AgentState
from app.agents.tools import search_with_retry
from app.redis_client import set_workspace
from app.logger import get_logger

log = get_logger()


def research_agent(state: AgentState) -> AgentState:
    """
    ResearchAgent:
    - Searches for info on LangGraph and CrewAI
    - Writes findings to Redis workspace
    - Logs every action
    """
    task_id = state["task_id"]
    prompt = state["prompt"]

    log.info({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "agent_name": "ResearchAgent",
        "action_details": f"Starting research for prompt: '{prompt}'",
    })

    findings = ""

    # ── Handle flaky test prompt ───────────────────
    if "__FLAKY_TEST__" in prompt:
        findings = search_with_retry(
            query="__FLAKY_TEST__",
            task_id=task_id,
        )
    else:
        # ── Normal research ────────────────────────
        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "ResearchAgent",
            "action_details": "Searching for LangGraph features",
        })
        langgraph_info = search_with_retry(
            query="LangGraph features",
            task_id=task_id,
        )

        log.info({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "agent_name": "ResearchAgent",
            "action_details": "Searching for CrewAI features",
        })
        crewai_info = search_with_retry(
            query="CrewAI features",
            task_id=task_id,
        )

        findings = f"=== LangGraph ===\n{langgraph_info}\n\n=== CrewAI ===\n{crewai_info}"

    # ── Write findings to Redis workspace ─────────
    set_workspace(task_id=task_id, data={
        "research_findings": findings,
        "researched_at": datetime.now(timezone.utc).isoformat(),
    })

    log.info({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "task_id": task_id,
        "agent_name": "ResearchAgent",
        "action_details": "Research complete. Findings saved to Redis workspace.",
    })

    # ── Update state ───────────────────────────────
    new_logs = state.get("agent_logs", []) + [{
        "agent": "ResearchAgent",
        "action": "Searching for LangGraph features",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }]

    return {
        **state,
        "research_findings": findings,
        "agent_logs": new_logs,
        "status": "RESEARCHED",
    }