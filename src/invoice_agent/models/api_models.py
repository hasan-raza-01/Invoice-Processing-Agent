"""API request/response models"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class WorkflowStartRequest(BaseModel):
    """Request to start a new workflow"""
    invoice_payload: Dict[str, Any] = Field(..., description="Invoice payload data")


class WorkflowStartResponse(BaseModel):
    """Response after starting workflow"""
    workflow_id: str = Field(..., description="Unique workflow ID")
    status: str = Field(..., description="Workflow status")
    current_stage: str = Field(..., description="Current stage")
    checkpoint_id: Optional[str] = Field(None, description="Checkpoint ID if paused")
    review_url: Optional[str] = Field(None, description="Review URL if paused")


class WorkflowStatusResponse(BaseModel):
    """Workflow status response"""
    workflow_id: str = Field(..., description="Workflow ID")
    invoice_id: str = Field(..., description="Invoice ID")
    status: str = Field(..., description="Current status")
    current_stage: str = Field(..., description="Current stage")
    logs: List[str] = Field(default_factory=list, description="Execution logs")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class PendingReviewItem(BaseModel):
    """Pending human review item"""
    checkpoint_id: str = Field(..., description="Checkpoint ID")
    invoice_id: str = Field(..., description="Invoice ID")
    vendor_name: str = Field(..., description="Vendor name")
    amount: float = Field(..., description="Invoice amount")
    reason_for_hold: str = Field(..., description="Reason for human review")
    review_url: str = Field(..., description="Review URL")
    created_at: datetime = Field(..., description="Creation timestamp")


class PendingReviewsResponse(BaseModel):
    """List of pending reviews"""
    items: List[PendingReviewItem] = Field(default_factory=list, description="Pending review items")


class DecisionRequest(BaseModel):
    """Human review decision request"""
    checkpoint_id: str = Field(..., description="Checkpoint ID")
    decision: str = Field(..., description="ACCEPT or REJECT")
    notes: Optional[str] = Field(None, description="Reviewer notes")
    reviewer_id: str = Field(..., description="Reviewer identifier")


class DecisionResponse(BaseModel):
    """Human review decision response"""
    checkpoint_id: str = Field(..., description="Checkpoint ID")
    decision: str = Field(..., description="Decision made")
    resume_token: str = Field(..., description="Resume token")
    next_stage: str = Field(..., description="Next stage")
    message: str = Field(..., description="Response message")
