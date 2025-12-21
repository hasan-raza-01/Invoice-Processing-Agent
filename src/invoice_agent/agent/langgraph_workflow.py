"""LangGraph workflow orchestrator"""
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from invoice_agent.models.state_models import WorkflowState
from invoice_agent.nodes.workflow_nodes_1 import (
    intake_node,
    understand_node,
    prepare_node,
    retrieve_node,
    match_two_way_node
)
from invoice_agent.nodes.workflow_nodes_2 import (
    checkpoint_hitl_node,
    hitl_decision_node,
    reconcile_node,
    approve_node,
    posting_node,
    notify_node,
    complete_node
)
from invoice_agent.utils.logger import logger


def route_after_match(state: WorkflowState) -> Literal["CHECKPOINT_HITL", "RECONCILE"]:
    """
    Route after MATCH_TWO_WAY based on match result
    
    If match failed -> CHECKPOINT_HITL
    If match succeeded -> RECONCILE
    """
    match_result = state.get("match_result", "FAILED")
    
    if match_result == "FAILED":
        logger.info("🔀 Routing to CHECKPOINT_HITL (match failed)")
        return "CHECKPOINT_HITL"
    else:
        logger.info("🔀 Routing to RECONCILE (match succeeded)")
        return "RECONCILE"


def route_after_hitl(state: WorkflowState) -> Literal["RECONCILE", "COMPLETE", END]:
    """
    Route after HITL_DECISION based on human decision
    
    If ACCEPT -> RECONCILE
    If REJECT -> COMPLETE (with MANUAL_HANDOFF status)
    If no decision yet -> END (workflow paused)
    """
    decision = state.get("human_decision")
    
    if decision == "ACCEPT":
        logger.info("🔀 Routing to RECONCILE (human accepted)")
        return "RECONCILE"
    elif decision == "REJECT":
        logger.info("🔀 Routing to COMPLETE (human rejected)")
        return "COMPLETE"
    else:
        logger.info("🔀 Workflow paused, waiting for human decision")
        return END


def create_workflow() -> StateGraph:
    """
    Create the complete LangGraph workflow with all nodes and edges
    
    Returns:
        Compiled LangGraph workflow
    """
    logger.info("Building LangGraph workflow...")
    
    # Initialize graph
    workflow = StateGraph(WorkflowState)
    
    # Add all 12 nodes
    workflow.add_node("INTAKE", intake_node)
    workflow.add_node("UNDERSTAND", understand_node)
    workflow.add_node("PREPARE", prepare_node)
    workflow.add_node("RETRIEVE", retrieve_node)
    workflow.add_node("MATCH_TWO_WAY", match_two_way_node)
    workflow.add_node("CHECKPOINT_HITL", checkpoint_hitl_node)
    workflow.add_node("HITL_DECISION", hitl_decision_node)
    workflow.add_node("RECONCILE", reconcile_node)
    workflow.add_node("APPROVE", approve_node)
    workflow.add_node("POSTING", posting_node)
    workflow.add_node("NOTIFY", notify_node)
    workflow.add_node("COMPLETE", complete_node)
    
    # Set entry point
    workflow.set_entry_point("INTAKE")
    
    # Add sequential edges (deterministic flow)
    workflow.add_edge("INTAKE", "UNDERSTAND")
    workflow.add_edge("UNDERSTAND", "PREPARE")
    workflow.add_edge("PREPARE", "RETRIEVE")
    workflow.add_edge("RETRIEVE", "MATCH_TWO_WAY")
    
    # Conditional edge after MATCH_TWO_WAY
    workflow.add_conditional_edges(
        "MATCH_TWO_WAY",
        route_after_match,
        {
            "CHECKPOINT_HITL": "CHECKPOINT_HITL",
            "RECONCILE": "RECONCILE"
        }
    )
    
    # Edge from CHECKPOINT to HITL_DECISION
    workflow.add_edge("CHECKPOINT_HITL", "HITL_DECISION")
    
    # Conditional edge after HITL_DECISION
    workflow.add_conditional_edges(
        "HITL_DECISION",
        route_after_hitl,
        {
            "RECONCILE": "RECONCILE",
            "COMPLETE": "COMPLETE",
            END: END
        }
    )
    
    # Continue sequential flow after RECONCILE
    workflow.add_edge("RECONCILE", "APPROVE")
    workflow.add_edge("APPROVE", "POSTING")
    workflow.add_edge("POSTING", "NOTIFY")
    workflow.add_edge("NOTIFY", "COMPLETE")
    workflow.add_edge("COMPLETE", END)
    
    # Compile workflow with Memory checkpoint saver
    checkpointer = MemorySaver()
    app = workflow.compile(checkpointer=checkpointer)
    
    logger.info("[OK] LangGraph workflow compiled successfully")
    return app


# Create the workflow instance
langgraph_app = create_workflow()
