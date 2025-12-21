"""LangGraph workflow nodes Part 2: Checkpoint, HITL, and completion stages"""
import sys
from datetime import datetime, timezone
import uuid
import os

from invoice_agent.models.state_models import WorkflowState
from invoice_agent.utils.logger import logger
from invoice_agent.utils.exceptions import InvoiceAgentException
from invoice_agent.bigtool.bigtool_picker import BigtoolPicker
from invoice_agent.mcp.common_client import CommonClient
from invoice_agent.mcp.atlas_client import AtlasClient
from invoice_agent.database.checkpoint_store import CheckpointStore

# Initialize clients
bigtool = BigtoolPicker()
common_client = CommonClient()
atlas_client = AtlasClient()
checkpoint_store = CheckpointStore()


def checkpoint_hitl_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 6: CHECKPOINT_HITL - Create checkpoint for human review
    """
    logger.info("=" * 60)
    logger.info("Stage 6: CHECKPOINT_HITL - Creating checkpoint")
    logger.info("=" * 60)
    
    try:
        # Generate checkpoint ID
        checkpoint_id = f"CKPT-{uuid.uuid4().hex[:8]}"
        
        # Create review URL
        app_url = os.getenv("APP_URL", "http://localhost:8501")
        review_url = f"{app_url}/review/{checkpoint_id}"
        paused_reason = f"2-way match failed: Score {state['match_score']:.2f} below threshold"
        
        # Save checkpoint to database
        checkpoint_store.save_checkpoint(
            checkpoint_id=checkpoint_id,
            state_blob=dict(state),
            invoice_id=state["invoice_id"],
            paused_reason=paused_reason
        )
        
        # Add to human review queue
        checkpoint_store.add_to_review_queue(
            checkpoint_id=checkpoint_id,
            invoice_id=state["invoice_id"],
            vendor_name=state["vendor_profile"]["normalized_name"],
            amount=state["invoice_payload"]["amount"],
            reason_for_hold=paused_reason,
            review_url=review_url
        )
        
        # Update state
        state["hitl_checkpoint_id"] = checkpoint_id
        state["review_url"] = review_url
        state["paused_reason"] = paused_reason
        state["status"] = "PAUSED"
        state["current_stage"] = "CHECKPOINT_HITL"
        state["logs"].append(f"[CHECKPOINT_HITL] Checkpoint created: {checkpoint_id}")
        
        logger.info(f"[PAUSED]  Checkpoint created - ID: {checkpoint_id}")
        logger.info(f"[INFO] Review URL: {review_url}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] CHECKPOINT_HITL failed: {e}")
        raise InvoiceAgentException(f"CHECKPOINT_HITL stage failed: {e}", sys)


def hitl_decision_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 7: HITL_DECISION - Wait for and process human decision
    """
    logger.info("=" * 60)
    logger.info("Stage 7: HITL_DECISION - Processing human decision")
    logger.info("=" * 60)
    
    try:
        # Check if decision has been made
        decision = state.get("human_decision")
        
        if not decision:
            # Still waiting for human
            state["status"] = "PAUSED"
            state["logs"].append("[HITL_DECISION] Waiting for human review")
            logger.info("[WAITING] Waiting for human decision...")
            return state
        
        # Decision received
        reviewer_id = state.get("reviewer_id", "unknown")
        
        if decision == "ACCEPT":
            state["next_stage"] = "RECONCILE"
            state["status"] = "RUNNING"
            state["logs"].append(f"[HITL_DECISION] Human approved by {reviewer_id}")
            logger.info(f"[OK] Human ACCEPTED invoice - Reviewer: {reviewer_id}")
            
        elif decision == "REJECT":
            state["next_stage"] = "COMPLETE"
            state["status"] = "MANUAL_HANDOFF"
            state["logs"].append(f"[HITL_DECISION] Human rejected by {reviewer_id}")
            logger.info(f"[ERROR] Human REJECTED invoice - Reviewer: {reviewer_id}")
        
        state["current_stage"] = "HITL_DECISION"
        state["resume_token"] = state["workflow_id"]
        
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] HITL_DECISION failed: {e}")
        raise InvoiceAgentException(f"HITL_DECISION stage failed: {e}", sys)


def reconcile_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 8: RECONCILE - Build accounting entries
    """
    logger.info("=" * 60)
    logger.info("Stage 8: RECONCILE - Building accounting entries")
    logger.info("=" * 60)
    
    try:
        amount = state["normalized_invoice"]["amount"]
        
        # Build accounting entries
        accounting_entries = [
            {
                "account": "AP_Payable",
                "type": "CREDIT",
                "amount": amount,
                "description": f"Invoice {state['invoice_id']}"
            },
            {
                "account": "Expenses",
                "type": "DEBIT",
                "amount": amount,
                "description": f"Invoice {state['invoice_id']}"
            }
        ]
        
        # Build reconciliation report
        reconciliation_report = {
            "invoice_total": amount,
            "po_total": state["matched_pos"][0]["amount"] if state["matched_pos"] else 0,
            "variance": 0,
            "reconciled": True
        }
        
        # Update state
        state["accounting_entries"] = accounting_entries
        state["reconciliation_report"] = reconciliation_report
        state["current_stage"] = "RECONCILE"
        state["logs"].append(f"[RECONCILE] Created {len(accounting_entries)} accounting entries")
        
        logger.info(f"[OK] Reconciliation completed - Entries: {len(accounting_entries)}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] RECONCILE failed: {e}")
        raise InvoiceAgentException(f"RECONCILE stage failed: {e}", sys)


def approve_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 9: APPROVE - Apply approval policy
    """
    logger.info("=" * 60)
    logger.info("Stage 9: APPROVE - Applying approval policy")
    logger.info("=" * 60)
    
    try:
        amount = state["normalized_invoice"]["amount"]
        approval_threshold = 5000.0
        
        if amount < approval_threshold:
            approval_status = "AUTO_APPROVED"
            approver_id = "SYSTEM"
        else:
            approval_status = "ESCALATED"
            approver_id = "MANAGER_001"
        
        # Update state
        state["approval_status"] = approval_status
        state["approver_id"] = approver_id
        state["current_stage"] = "APPROVE"
        state["logs"].append(f"[APPROVE] Status: {approval_status}")
        
        logger.info(f"[OK] Approval: {approval_status}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] APPROVE failed: {e}")
        raise InvoiceAgentException(f"APPROVE stage failed: {e}", sys)


def posting_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 10: POSTING - Post to ERP and schedule payment
    """
    logger.info("=" * 60)
    logger.info("Stage 10: POSTING - Posting to ERP")
    logger.info("=" * 60)
    
    try:
        # Select ERP tool
        erp_tool = bigtool.select("erp_connector")
        
        # Post to ERP (ATLAS)
        post_result = atlas_client.post_to_erp(
            state["accounting_entries"],
            erp_tool
        )
        
        # Schedule payment (ATLAS)
        payment_data = {
            "amount": state["normalized_invoice"]["amount"],
            "due_date": state["parsed_invoice"]["parsed_dates"]["due_date"],
            "vendor_id": state["vendor_profile"]["tax_id"]
        }
        payment_result = atlas_client.schedule_payment(payment_data)
        
        # Update state
        state["posted"] = post_result["posted"]
        state["erp_txn_id"] = post_result["erp_txn_id"]
        state["scheduled_payment_id"] = payment_result["scheduled_payment_id"]
        state["current_stage"] = "POSTING"
        state["logs"].append(f"[POSTING] Posted to ERP: {post_result['erp_txn_id']}")
        
        logger.info(f"[OK] Posted to ERP - TXN: {post_result['erp_txn_id']}")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] POSTING failed: {e}")
        raise InvoiceAgentException(f"POSTING stage failed: {e}", sys)


def notify_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 11: NOTIFY - Send notifications
    """
    logger.info("=" * 60)
    logger.info("Stage 11: NOTIFY - Sending notifications")
    logger.info("=" * 60)
    
    try:
        # Select email tool
        email_tool = bigtool.select("email")
        
        # Notify vendor (ATLAS)
        vendor_notification = atlas_client.send_notification(
            recipient=f"{state['vendor_profile']['normalized_name']}@vendor.com",
            message=f"Invoice {state['invoice_id']} processed successfully. Payment scheduled.",
            email_tool=email_tool
        )
        
        # Notify finance team (ATLAS)
        finance_notification = atlas_client.send_notification(
            recipient="finance@company.com",
            message=f"Invoice {state['invoice_id']} approved and posted. TXN: {state['erp_txn_id']}",
            email_tool=email_tool
        )
        
        # Update state
        state["notify_status"] = {
            "vendor": vendor_notification["sent"],
            "finance": finance_notification["sent"]
        }
        state["notified_parties"] = [
            vendor_notification["recipient"],
            finance_notification["recipient"]
        ]
        state["current_stage"] = "NOTIFY"
        state["logs"].append(f"[NOTIFY] Notifications sent to {len(state['notified_parties'])} parties")
        
        logger.info(f"[OK] Notifications sent to {len(state['notified_parties'])} parties")
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] NOTIFY failed: {e}")
        raise InvoiceAgentException(f"NOTIFY stage failed: {e}", sys)


def complete_node(state: WorkflowState) -> WorkflowState:
    """
    Stage 12: COMPLETE - Finalize workflow
    """
    logger.info("=" * 60)
    logger.info("Stage 12: COMPLETE - Finalizing workflow")
    logger.info("=" * 60)
    
    try:
        # Build final payload
        final_payload = {
            "workflow_id": state["workflow_id"],
            "invoice_id": state["invoice_id"],
            "vendor": state["vendor_profile"]["normalized_name"],
            "amount": state["normalized_invoice"]["amount"],
            "erp_txn_id": state.get("erp_txn_id"),
            "payment_id": state.get("scheduled_payment_id"),
            "status": state["status"],
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Mark status
        if state["status"] != "MANUAL_HANDOFF":
            state["status"] = "COMPLETED"
        
        # Update state
        state["final_payload"] = final_payload
        state["current_stage"] = "COMPLETE"
        state["logs"].append(f"[COMPLETE] Workflow finished with status: {state['status']}")
        
        # Log audit
        try:
            checkpoint_store.log_audit(
                workflow_id=state["workflow_id"],
                invoice_id=state["invoice_id"],
                stage="COMPLETE",
                action="workflow_completed",
                details=final_payload
            )
        except:
            pass  # Non-critical
        
        logger.info(f"[COMPLETE] Workflow COMPLETE - Status: {state['status']}")
        logger.info("=" * 60)
        return state
        
    except Exception as e:
        logger.error(f"[ERROR] COMPLETE failed: {e}")
        raise InvoiceAgentException(f"COMPLETE stage failed: {e}", sys)
