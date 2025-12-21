"""Workflow state models for LangGraph"""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from datetime import datetime
import operator


class WorkflowState(TypedDict):
    """Complete workflow state passed between LangGraph nodes"""
    
    # Identity
    workflow_id: str
    invoice_id: str
    
    # Raw Input
    invoice_payload: Dict[str, Any]
    
    # Stage 1: INTAKE
    raw_id: Optional[str]
    ingest_ts: Optional[str]
    validated: Optional[bool]
    
    # Stage 2: UNDERSTAND
    parsed_invoice: Optional[Dict[str, Any]]
    
    # Stage 3: PREPARE
    vendor_profile: Optional[Dict[str, Any]]
    normalized_invoice: Optional[Dict[str, Any]]
    flags: Optional[Dict[str, Any]]
    
    # Stage 4: RETRIEVE
    matched_pos: Optional[List[Dict[str, Any]]]
    matched_grns: Optional[List[Dict[str, Any]]]
    history: Optional[List[Dict[str, Any]]]
    
    # Stage 5: MATCH_TWO_WAY
    match_score: Optional[float]
    match_result: Optional[str]  # "MATCHED" or "FAILED"
    tolerance_pct: Optional[float]
    match_evidence: Optional[Dict[str, Any]]
    
    # Stage 6: CHECKPOINT_HITL
    hitl_checkpoint_id: Optional[str]
    review_url: Optional[str]
    paused_reason: Optional[str]
    
    # Stage 7: HITL_DECISION
    human_decision: Optional[str]  # "ACCEPT" or "REJECT"
    reviewer_id: Optional[str]
    resume_token: Optional[str]
    next_stage: Optional[str]
    
    # Stage 8: RECONCILE
    accounting_entries: Optional[List[Dict[str, Any]]]
    reconciliation_report: Optional[Dict[str, Any]]
    
    # Stage 9: APPROVE
    approval_status: Optional[str]
    approver_id: Optional[str]
    
    # Stage 10: POSTING
    posted: Optional[bool]
    erp_txn_id: Optional[str]
    scheduled_payment_id: Optional[str]
    
    # Stage 11: NOTIFY
    notify_status: Optional[Dict[str, str]]
    notified_parties: Optional[List[str]]
    
    # Stage 12: COMPLETE
    final_payload: Optional[Dict[str, Any]]
    audit_log: Annotated[List[str], operator.add]  # Accumulate logs
    status: str  # RUNNING, PAUSED, COMPLETED, FAILED, MANUAL_HANDOFF
    
    # Metadata
    current_stage: str
    timestamp: str
    logs: Annotated[List[str], operator.add]  # Accumulate logs across nodes
