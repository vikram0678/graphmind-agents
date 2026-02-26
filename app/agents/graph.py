from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.research_agent import research_agent
from app.agents.writing_agent import writing_agent


def should_continue_after_approval(state: AgentState) -> str:
    """Route after approval check."""
    if state.get("approved") is True:
        return "complete"
    return "wait"


def approval_node(state: AgentState) -> AgentState:
    """Pause node — waits for human approval via Redis."""
    return {
        **state,
        "status": "AWAITING_APPROVAL",
    }


def completion_node(state: AgentState) -> AgentState:
    """Final node — marks task as completed."""
    return {
        **state,
        "result": state.get("draft_summary", ""),
        "status": "COMPLETED",
    }


def build_graph() -> StateGraph:
    """Build and compile the LangGraph state machine."""

    graph = StateGraph(AgentState)

    # ── Add nodes ──────────────────────────────────
    graph.add_node("research", research_agent)
    graph.add_node("write", writing_agent)
    graph.add_node("await_approval", approval_node)
    graph.add_node("complete", completion_node)

    # ── Add edges ──────────────────────────────────
    graph.set_entry_point("research")
    graph.add_edge("research", "write")
    graph.add_edge("write", "await_approval")
    graph.add_edge("await_approval", END)
    graph.add_edge("complete", END)

    return graph.compile()