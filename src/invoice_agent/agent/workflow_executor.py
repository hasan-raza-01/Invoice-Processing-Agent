"""Workflow execution helpers"""
import uuid
from datetime import datetime, timezone
from typing import Dict, Any

from invoice_agent.models.state_models import WorkflowState
from invoice_agent.agent.langgraph_workflow import langgraph_app
from invoice_agent.database.checkpoint_store import CheckpointStore
from invoice_agent.utils.logger import logger


async def start_workflow(invoice_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Start a new invoice processing workflow
    
    Args:
        invoice_payload: Invoice data
        
    Returns:
        Workflow result with status and checkpoint info
    """
    # Generate workflow ID
    workflow_id = str(uuid.uuid4())
    invoice_id = invoice_payload.get("invoice_id", f"INV-{uuid.uuid4().hex[:8]}")
    
    logger.info(f"🚀 Starting workflow: {workflow_id}")
    logger.info(f"📄 Invoice ID: {invoice_id}")
    
    # Initialize state
    initial_state: WorkflowState = {
        "workflow_id": workflow_id,
        "invoice_id": invoice_id,
        "invoice_payload": invoice_payload,
        "raw_id": None,
        "ingest_ts": None,
        "validated": None,
        "parsed_invoice": None,
        "vendor_profile": None,
        "normalized_invoice": None,
        "flags": None,
        "matched_pos": None,
        "matched_grns": None,
        "history": None,
        "match_score": None,
        "match_result": None,
        "tolerance_pct": None,
        "match_evidence": None,
        "hitl_checkpoint_id": None,
        "review_url": None,
        "paused_reason": None,
        "human_decision": None,
        "reviewer_id": None,
        "resume_token": None,
        "next_stage": None,
        "accounting_entries": None,
        "reconciliation_report": None,
        "approval_status": None,
        "approver_id": None,
        "posted": None,
        "erp_txn_id": None,
        "scheduled_payment_id": None,
        "notify_status": None,
        "notified_parties": None,
        "final_payload": None,
        "audit_log": [],
        "status": "RUNNING",
        "current_stage": "START",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "logs": []
    }
    
    # Run workflow
    config = {"configurable": {"thread_id": workflow_id}}
    result = await langgraph_app.ainvoke(initial_state, config)
    
    logger.info(f"[OK] Workflow execution completed - Status: {result['status']}")
    
    return {
        "workflow_id": workflow_id,
        "invoice_id": invoice_id,
        "status": result["status"],
        "current_stage": result["current_stage"],
        "review_checkpoint_id": result.get("hitl_checkpoint_id"),
        "review_url": result.get("review_url"),
        "logs": result.get("logs", [])
    }


async def resume_workflow(checkpoint_id: str, human_decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resume workflow after human review
    
    FIXED: Instead of using langgraph_app.ainvoke() which hangs,
    we manually execute the remaining workflow nodes sequentially.
    
    Args:
        checkpoint_id: Checkpoint identifier
        human_decision: Human decision data (decision, reviewer_id, notes)
        
    Returns:
        Workflow result
    """
    logger.info(f"[RESUME] Resuming workflow from checkpoint: {checkpoint_id}")
    
    checkpoint_store = None
    try:
        # Load checkpoint state
        checkpoint_store = CheckpointStore()
        state = checkpoint_store.load_checkpoint(checkpoint_id)
        
        if not state:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")
        
        # Inject human decision
        state["human_decision"] = human_decision["decision"]
        state["reviewer_id"] = human_decision.get("reviewer_id", "unknown")
        state["status"] = "RUNNING"
        state["logs"].append(f"[RESUME] Human decision: {human_decision['decision']}")
        
        # Update checkpoint in DB
        try:
            checkpoint_store.update_checkpoint_decision(
                checkpoint_id=checkpoint_id,
                decision=human_decision["decision"],
                reviewer_id=human_decision.get("reviewer_id", "unknown")
            )
        except Exception as e:
            logger.error(f"Failed to update checkpoint decision: {e}")
            # Continue anyway
        
        # Update review queue
        try:
            status = "APPROVED" if human_decision["decision"] == "ACCEPT" else "REJECTED"
            checkpoint_store.update_review_status(checkpoint_id, status)
        except Exception as e:
            logger.error(f"Failed to update review queue status: {e}")
            # Continue anyway
        
        # CRITICAL FIX: Don't use langgraph_app.ainvoke() - it hangs!
        # Instead, manually execute remaining nodes based on decision
        try:
            if human_decision["decision"] == "ACCEPT":
                # Execute remaining nodes: RECONCILE -> APPROVE -> POSTING -> NOTIFY -> COMPLETE
                from invoice_agent.nodes.workflow_nodes_2 import (
                    reconcile_node,
                    approve_node,
                    posting_node,
                    notify_node,
                    complete_node
                )
                
                logger.info("[RESUME] Executing remaining workflow nodes after ACCEPT")
                
                state = reconcile_node(state)
                state = approve_node(state)
                state = posting_node(state)
                state = notify_node(state)
                state = complete_node(state)
                
                result = state
            else:
                # REJECT: Skip to COMPLETE with MANUAL_HANDOFF status
                from invoice_agent.nodes.workflow_nodes_2 import complete_node
                
                logger.info("[RESUME] Executing COMPLETE node after REJECT")
                state["status"] = "MANUAL_HANDOFF"
                state["logs"].append("[REJECT] Invoice rejected by human reviewer - manual handling required")
                result = complete_node(state)
                
        except Exception as e:
            logger.error(f"Error during manual node execution: {e}", exc_info=True)
            # Return error state instead of crashing
            return {
                "workflow_id": state.get("workflow_id", "unknown"),
                "status": "ERROR",
                "current_stage": state.get("current_stage", "UNKNOWN"),
                "next_stage": None,
                "error": str(e),
                "logs": state.get("logs", []) + [f"[ERROR] Workflow resume failed: {e}"]
            }
        
        logger.info(f"[OK] Workflow resumed - Final Status: {result['status']}")
        
        return {
            "workflow_id": result["workflow_id"],
            "status": result["status"],
            "current_stage": result["current_stage"],
            "next_stage": result.get("next_stage") or "COMPLETED",  # Default to COMPLETED if None
            "logs": result.get("logs", [])
        }
        
    except Exception as e:
        logger.error(f"Critical error in resume_workflow: {e}", exc_info=True)
        raise
    finally:
        if checkpoint_store:
            checkpoint_store.close()
