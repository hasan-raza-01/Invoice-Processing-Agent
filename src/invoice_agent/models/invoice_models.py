"""Invoice data models using Pydantic"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class LineItem(BaseModel):
    """Individual line item in an invoice"""
    desc: str = Field(..., description="Item description")
    qty: float = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    total: float = Field(..., description="Total amount for this line item")


class InvoicePayload(BaseModel):
    """Input invoice payload schema"""
    invoice_id: str = Field(..., description="Unique invoice identifier")
    vendor_name: str = Field(..., description="Vendor/supplier name")
    vendor_tax_id: str = Field(..., description="Vendor tax ID (PAN/GST/TIN)")
    invoice_date: str = Field(..., description="Invoice date (ISO format)")
    due_date: str = Field(..., description="Payment due date (ISO format)")
    amount: float = Field(..., description="Total invoice amount")
    currency: str = Field(default="USD", description="Currency code")
    line_items: List[LineItem] = Field(..., description="Invoice line items")
    attachments: List[str] = Field(default_factory=list, description="Attachment URLs/paths")


class ParsedInvoice(BaseModel):
    """Parsed invoice data from OCR"""
    invoice_text: str = Field(..., description="Extracted text from OCR")
    parsed_line_items: List[Dict[str, Any]] = Field(..., description="Parsed line items")
    detected_pos: List[str] = Field(default_factory=list, description="Detected PO references")
    currency: str = Field(..., description="Currency code")
    parsed_dates: Dict[str, str] = Field(..., description="Parsed dates")


class VendorProfile(BaseModel):
    """Vendor profile after normalization and enrichment"""
    normalized_name: str = Field(..., description="Normalized vendor name")
    tax_id: str = Field(..., description="Tax ID")
    enrichment_meta: Dict[str, Any] = Field(default_factory=dict, description="Enrichment metadata")


class Flags(BaseModel):
    """Validation and risk flags"""
    missing_info: List[str] = Field(default_factory=list, description="Missing information flags")
    risk_score: float = Field(default=0.0, description="Risk score (0-1)")


class NormalizedInvoice(BaseModel):
    """Normalized invoice data"""
    amount: float = Field(..., description="Normalized amount")
    currency: str = Field(..., description="Currency code")
    line_items: List[LineItem] = Field(..., description="Normalized line items")


class PurchaseOrder(BaseModel):
    """Purchase Order data"""
    po_id: str = Field(..., description="PO ID")
    vendor_name: str = Field(..., description="Vendor name")
    amount: float = Field(..., description="PO amount")
    line_items: List[LineItem] = Field(default_factory=list, description="PO line items")
    status: str = Field(default="OPEN", description="PO status")


class GoodsReceivedNote(BaseModel):
    """Goods Received Note data"""
    grn_id: str = Field(..., description="GRN ID")
    po_id: str = Field(..., description="Related PO ID")
    received_qty: float = Field(..., description="Received quantity")
    status: str = Field(default="RECEIVED", description="GRN status")


class MatchResult(BaseModel):
    """2-way match result"""
    match_score: float = Field(..., description="Match score (0-1)")
    match_result: str = Field(..., description="MATCHED or FAILED")
    tolerance_pct: float = Field(..., description="Tolerance percentage")
    match_evidence: Dict[str, Any] = Field(default_factory=dict, description="Match evidence details")


class CheckpointInfo(BaseModel):
    """Checkpoint information"""
    checkpoint_id: str = Field(..., description="Unique checkpoint ID")
    review_url: str = Field(..., description="URL for human review")
    paused_reason: str = Field(..., description="Reason for pause")


class HumanDecision(BaseModel):
    """Human review decision"""
    human_decision: str = Field(..., description="ACCEPT or REJECT")
    reviewer_id: str = Field(..., description="Reviewer identifier")
    resume_token: str = Field(..., description="Token to resume workflow")
    next_stage: str = Field(..., description="Next stage to execute")
    notes: Optional[str] = Field(None, description="Reviewer notes")


class AccountingEntry(BaseModel):
    """Accounting entry (debit/credit)"""
    account: str = Field(..., description="GL account")
    type: str = Field(..., description="DEBIT or CREDIT")
    amount: float = Field(..., description="Amount")


class ApprovalStatus(BaseModel):
    """Approval status"""
    approval_status: str = Field(..., description="AUTO_APPROVED or ESCALATED")
    approver_id: Optional[str] = Field(None, description="Approver ID if escalated")


class PostingResult(BaseModel):
    """Posting result"""
    posted: bool = Field(..., description="Whether posted successfully")
    erp_txn_id: str = Field(..., description="ERP transaction ID")
    scheduled_payment_id: Optional[str] = Field(None, description="Scheduled payment ID")


class NotificationStatus(BaseModel):
    """Notification status"""
    notify_status: Dict[str, str] = Field(default_factory=dict, description="Notification statuses")
    notified_parties: List[str] = Field(default_factory=list, description="Notified parties")


class FinalPayload(BaseModel):
    """Final workflow output"""
    workflow_id: str = Field(..., description="Workflow ID")
    invoice_id: str = Field(..., description="Invoice ID")
    status: str = Field(..., description="Final status")
    final_payload: Dict[str, Any] = Field(..., description="Complete workflow data")
    audit_log: List[str] = Field(default_factory=list, description="Audit log entries")
    timestamp: datetime = Field(default_factory=datetime.now, description="Completion timestamp")
