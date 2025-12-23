"""Checkpoint store for persisting and loading workflow state"""
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import json
import uuid

from invoice_agent.database.models import (
    Checkpoint,
    HumanReviewQueue,
    AuditLog,
    get_session
)
from invoice_agent.utils.logger import logger
from invoice_agent.utils.exceptions import InvoiceAgentException
import sys


class CheckpointStore:
    """Manages checkpoint persistence and retrieval"""
    
    def __init__(self):
        """Initialize checkpoint store"""
        # Note: get_session is now a context manager, so we don't store it
        pass
    
    def save_checkpoint(
        self,
        checkpoint_id: str,
        state_blob: Dict[str, Any],
        invoice_id: str,
        paused_reason: str
    ) -> str:
        """
        Save checkpoint to database
        
        Args:
            checkpoint_id: Unique checkpoint identifier
            state_blob: Complete workflow state
            invoice_id: Invoice ID
            paused_reason: Reason for pausing
            
        Returns:
            checkpoint_id
        """
        try:
            with get_session() as session:
                checkpoint = Checkpoint(
                    checkpoint_id=checkpoint_id,
                    invoice_id=invoice_id,
                    workflow_id=state_blob.get("workflow_id", ""),
                    state_blob=state_blob,  # SQLAlchemy will handle JSON serialization
                    paused_reason=paused_reason,
                    status="PENDING"
                )
                
                session.add(checkpoint)
                # Commit is handled by context manager
                
                logger.info(f"Checkpoint saved: {checkpoint_id}")
                return checkpoint_id
            
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
            raise InvoiceAgentException(f"Failed to save checkpoint: {e}", sys)
    
    def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint state from database
        
        Args:
            checkpoint_id: Checkpoint identifier
            
        Returns:
            State blob or None if not found
        """
        try:
            with get_session() as session:
                checkpoint = session.query(Checkpoint).filter_by(
                    checkpoint_id=checkpoint_id
                ).first()
                
                if checkpoint:
                    return checkpoint.state_blob
                return None
            
        except Exception as e:
            logger.error(f"Error loading checkpoint: {e}")
            raise InvoiceAgentException(f"Failed to load checkpoint: {e}", sys)
    
    def update_checkpoint_decision(
        self,
        checkpoint_id: str,
        decision: str,
        reviewer_id: str
    ):
        """
        Update checkpoint with human decision
        
        Args:
            checkpoint_id: Checkpoint identifier
            decision: ACCEPT or REJECT
            reviewer_id: Reviewer identifier
        """
        try:
            with get_session() as session:
                checkpoint = session.query(Checkpoint).filter_by(
                    checkpoint_id=checkpoint_id
                ).first()
                
                if checkpoint:
                    checkpoint.decision = decision
                    checkpoint.reviewer_id = reviewer_id
                    checkpoint.resumed_at = datetime.now(timezone.utc)
                    checkpoint.status = "RESOLVED" if decision == "ACCEPT" else "REJECTED"
                    
                    # Commit is handled by context manager
                    logger.info(f"Checkpoint decision updated: {checkpoint_id} - {decision}")
                else:
                    raise ValueError(f"Checkpoint not found: {checkpoint_id}")
                
        except Exception as e:
            logger.error(f"Error updating checkpoint decision: {e}")
            raise InvoiceAgentException(f"Failed to update checkpoint: {e}", sys)
    
    def add_to_review_queue(
        self,
        checkpoint_id: str,
        invoice_id: str,
        vendor_name: str,
        amount: float,
        reason_for_hold: str,
        review_url: str
    ):
        """
        Add item to human review queue
        
        Args:
            checkpoint_id: Checkpoint identifier
            invoice_id: Invoice ID
            vendor_name: Vendor name
            amount: Invoice amount
            reason_for_hold: Reason for human review
            review_url: URL for review
        """
        try:
            with get_session() as session:
                review_item = HumanReviewQueue(
                    checkpoint_id=checkpoint_id,
                    invoice_id=invoice_id,
                    vendor_name=vendor_name,
                    amount=amount,
                    reason_for_hold=reason_for_hold,
                    review_url=review_url,
                    status="PENDING"
                )
                
                session.add(review_item)
                # Commit is handled by context manager
                
                logger.info(f"Added to review queue: {checkpoint_id}")
            
        except Exception as e:
            logger.error(f"Error adding to review queue: {e}")
            raise InvoiceAgentException(f"Failed to add to review queue: {e}", sys)
    
    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """
        Get all pending review items
        
        Returns:
            List of pending review items
        """
        try:
            with get_session() as session:
                reviews = session.query(HumanReviewQueue).filter_by(
                    status="PENDING"
                ).all()
                
                return [
                    {
                        "checkpoint_id": r.checkpoint_id,
                        "invoice_id": r.invoice_id,
                        "vendor_name": r.vendor_name,
                        "amount": r.amount,
                        "reason_for_hold": r.reason_for_hold,
                        "review_url": r.review_url,
                        "created_at": r.created_at.isoformat() if r.created_at else None
                    }
                    for r in reviews
                ]
            
        except Exception as e:
            logger.error(f"Error getting pending reviews: {e}")
            raise InvoiceAgentException(f"Failed to get pending reviews: {e}", sys)
    
    def update_review_status(self, checkpoint_id: str, status: str):
        """
        Update review queue item status
        
        Args:
            checkpoint_id: Checkpoint identifier
            status: New status (APPROVED, REJECTED)
        """
        try:
            with get_session() as session:
                review = session.query(HumanReviewQueue).filter_by(
                    checkpoint_id=checkpoint_id
                ).first()
                
                if review:
                    review.status = status
                    review.reviewed_at = datetime.now(timezone.utc)
                    # Commit is handled by context manager
                    logger.info(f"Review status updated: {checkpoint_id} - {status}")
                else:
                    # WARNING: Review not found, but don't raise exception
                    # This could happen if checkpoint was created but not added to queue
                    logger.warning(f"Review queue item not found for checkpoint: {checkpoint_id}")
                
        except Exception as e:
            logger.error(f"Error updating review status: {e}")
            # Don't raise exception to prevent crashing the workflow
            logger.warning(f"Continuing despite review status update failure")
    
    def log_audit(
        self,
        workflow_id: str,
        invoice_id: str,
        stage: str,
        action: str,
        details: Dict[str, Any]
    ):
        """
        Log audit entry
        
        Args:
            workflow_id: Workflow identifier
            invoice_id: Invoice ID
            stage: Stage name
            action: Action performed
            details: Additional details
        """
        try:
            with get_session() as session:
                audit = AuditLog(
                    workflow_id=workflow_id,
                    invoice_id=invoice_id,
                    stage=stage,
                    action=action,
                    details=details
                )
                
                session.add(audit)
                # Commit is handled by context manager
            
        except Exception as e:
            logger.error(f"Error logging audit: {e}")
    
    def close(self):
        """Close database session - no longer needed with context managers"""
        pass
