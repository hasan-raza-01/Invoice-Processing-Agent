"""FastAPI main application"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from invoice_agent.api.routes import workflow, human_review
from invoice_agent.utils.logger import logger
from invoice_agent.database.models import init_db

# Initialize database
init_db()
logger.info("[OK] Database initialized")

# Create FastAPI app
app = FastAPI(
    title="Invoice Processing Agent API",
    description="LangGraph-powered invoice processing with HITL checkpoints",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflow.router, prefix="/workflow", tags=["Workflow"])
app.include_router(human_review.router, prefix="/human-review", tags=["Human Review"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Invoice Processing Agent API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "invoice-processing-agent"
    }


if __name__ == "__main__":
    uvicorn.run(
        "invoice_agent.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
