"""FastAPI human review routes"""
from fastapi import APIRouter, HTTPException

from invoice_agent.models.api_models import (
    PendingReviewsResponse,
    PendingReviewItem,
    DecisionRequest,
    DecisionResponse
)
from invoice_agent.database.checkpoint_store import CheckpointStore
from invoice_agent.agent.workflow_executor import resume_workflow
from invoice_agent.utils.logger import logger

router = APIRouter()


@router.get("/pending", response_model=PendingReviewsResponse)
async def get_pending_reviews():
    """
    Get all pending human review items
    
    Returns:
        List of pending reviews
    """
    try:
        checkpoint_store = CheckpointStore()
        reviews = checkpoint_store.get_pending_reviews()
        checkpoint_store.close()
        
        items = [
            PendingReviewItem(
                checkpoint_id=r["checkpoint_id"],
                invoice_id=r["invoice_id"],
                vendor_name=r["vendor_name"],
                amount=r["amount"],
                reason_for_hold=r["reason_for_hold"],
                review_url=r["review_url"],
                created_at=r["created_at"]
            )
            for r in reviews
        ]
        
        logger.info(f"[INFO] Retrieved {len(items)} pending reviews")
        return PendingReviewsResponse(items=items)
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decision", response_model=DecisionResponse)
async def submit_decision(request: DecisionRequest):
    """
    Submit human review decision and resume workflow
    
    Args:
        request: Decision data
        
    Returns:
        Resume result
    """
    try:
        logger.info(f"[RECEIVED] Received decision for checkpoint: {request.checkpoint_id}")
        logger.info(f"   Decision: {request.decision}, Reviewer: {request.reviewer_id}")
        
        # Resume workflow
        human_decision = {
            "decision": request.decision,
            "reviewer_id": request.reviewer_id,
            "notes": request.notes
        }
        
        result = await resume_workflow(request.checkpoint_id, human_decision)
        
        return DecisionResponse(
            checkpoint_id=request.checkpoint_id,
            decision=request.decision,
            resume_token=result["workflow_id"],
            next_stage=result.get("next_stage", result["current_stage"]),
            message=f"Workflow resumed successfully with decision: {request.decision}"
        )
        
    except Exception as e:
        logger.error(f"Failed to process decision: {e}")
        raise HTTPException(status_code=500, detail=str(e))
