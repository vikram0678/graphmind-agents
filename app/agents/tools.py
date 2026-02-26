import time
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# ── Flaky tool state (resets per process) ─────────
_flaky_call_counts: dict = {}


def web_search(query: str, task_id: str = "") -> str:
    """
    Simulated web search tool.
    For query '__FLAKY_TEST__': fails on first call, succeeds on second.
    """
    # ── Flaky behavior for resilience test ────────
    if query == "__FLAKY_TEST__":
        count = _flaky_call_counts.get(task_id, 0)
        _flaky_call_counts[task_id] = count + 1

        if count == 0:
            logger.warning(
                f"[task:{task_id}] Flaky tool FAILED on first attempt for query='{query}'"
            )
            raise Exception(f"Simulated tool failure for query: {query}")

        logger.info(
            f"[task:{task_id}] Flaky tool SUCCEEDED on retry for query='{query}'"
        )
        return "Flaky test passed: This is the successful retry result."

    # ── Normal search results ──────────────────────
    search_results = {
        "langgraph": """
LangGraph Key Features:
- Stateful graph-based orchestration for LLM agents
- Built on LangChain, supports cycles and branching
- Native support for human-in-the-loop workflows
- Persistent checkpointing for long-running tasks
- Conditional edges for dynamic routing between nodes
- Supports multi-agent collaboration patterns
- Built-in streaming for real-time output
- First-class async support
        """.strip(),

        "crewai": """
CrewAI Key Features:
- Role-based agent design with defined personas
- Sequential and hierarchical task execution
- Built-in agent memory and context sharing
- Tool integration for web search, file ops, etc.
- Crew orchestration with manager agents
- Process types: sequential, hierarchical, consensual
- Easy to define agent goals and backstories
- Strong focus on agent collaboration and delegation
        """.strip(),
    }

    result = ""
    query_lower = query.lower()

    for keyword, content in search_results.items():
        if keyword in query_lower:
            result += content + "\n\n"

    if not result:
        result = f"General search results for: {query}\nFound relevant information about the topic."

    return result.strip()


def search_with_retry(query: str, task_id: str = "", max_retries: int = 3) -> str:
    """
    Web search with automatic retry on failure.
    Logs each attempt and retry.
    """
    from app.logger import get_logger
    log = get_logger()

    for attempt in range(1, max_retries + 1):
        try:
            log.info({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "agent_name": "ResearchAgent",
                "action_details": f"Searching for '{query}' (attempt {attempt})",
            })

            result = web_search(query=query, task_id=task_id)
            return result

        except Exception as e:
            log.warning({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "task_id": task_id,
                "agent_name": "ResearchAgent",
                "status": "tool_error",
                "action_details": f"Tool failed on attempt {attempt}: {str(e)}",
            })

            if attempt < max_retries:
                log.info({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "task_id": task_id,
                    "agent_name": "ResearchAgent",
                    "action_details": f"Retrying web search... (attempt {attempt + 1})",
                })
                time.sleep(1)
            else:
                raise Exception(
                    f"Tool failed after {max_retries} attempts: {str(e)}"
                )