"""FastAPI workflow routes"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from invoice_agent.models.api_models import (
    WorkflowStartRequest,
    WorkflowStartResponse
)
from invoice_agent.agent.workflow_executor import start_workflow
from invoice_agent.utils.logger import logger

router = APIRouter()


@router.post("/start", response_model=WorkflowStartResponse)
async def start_workflow_endpoint(request: WorkflowStartRequest):
    """
    Start a new invoice processing workflow
    
    Args:
        request: Invoice payload
        
    Returns:
        Workflow status with ID and checkpoint info
    """
    try:
        logger.info("📨 Received workflow start request")
        
        result = await start_workflow(request.invoice_payload)
        
        return WorkflowStartResponse(
            workflow_id=result["workflow_id"],
            status=result["status"],
            current_stage=result["current_stage"],
            checkpoint_id=result.get("hitl_checkpoint_id"),
            review_url=result.get("review_url")
        )
        
    except Exception as e:
        logger.error(f"Failed to start workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """
    Get workflow status
    
    Args:
        workflow_id: Workflow identifier
        
    Returns:
        Workflow status and logs
    """
    try:
        # This would query the checkpoint store or state
        # For simplicity, returning a basic response
        return {
            "workflow_id": workflow_id,
            "status": "Check logs or database for full status",
            "message": "Workflow status endpoint"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
