from typing import TypedDict, Optional, List


class AgentState(TypedDict):
    """Shared state passed between all agents in the graph."""
    task_id: str
    prompt: str
    research_findings: Optional[str]
    draft_summary: Optional[str]
    agent_logs: List[dict]
    status: str
    result: Optional[str]
    approved: Optional[bool]
    feedback: Optional[str]
    error: Optional[str]