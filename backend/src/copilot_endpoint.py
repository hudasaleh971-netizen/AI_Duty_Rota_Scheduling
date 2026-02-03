"""
CopilotKit Remote Endpoint with LangGraph Agent

This module sets up the CopilotKit integration using AG-UI protocol.
It provides a LangGraph-based chat agent for form filling assistance.

Usage:
    Mount this in your FastAPI app:
    
    from src.copilot_endpoint import copilot_app
    app.mount("/copilotkit", copilot_app)
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any

from copilotkit import LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint

from src.langgraph_agent import graph
from src.agents import RotaFillingAgent, UnitFillingAgent


# =============================================================================
# Initialize Agents (for direct API access)
# =============================================================================

rota_agent = RotaFillingAgent()
unit_agent = UnitFillingAgent()


# =============================================================================
# FastAPI App
# =============================================================================

copilot_app = FastAPI(
    title="CopilotKit Agent Endpoint",
    description="LangGraph-based AI agents for form filling assistance"
)

# CORS for CopilotKit frontend
copilot_app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4000",
        "http://localhost:5173",
        "http://localhost:5175"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add LangGraph agent endpoint using new AG-UI approach
add_langgraph_fastapi_endpoint(
    app=copilot_app,
    agent=LangGraphAGUIAgent(
        name="default",  # 'default' is required for CopilotKit auto-discovery
        description="AI assistant for filling rota and unit configuration forms. Can process uploaded files (Excel, Word, PDF) to extract schedule data, staff lists, and shift codes.",
        graph=graph
    ),
    path="/"  # Mount at root since we're already under /copilotkit
)


# =============================================================================
# Additional Endpoints (Direct API Access - kept for backwards compatibility)
# =============================================================================

@copilot_app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": ["default"],
        "copilotkit": "enabled",
        "framework": "langgraph"
    }


class AgentResponse(BaseModel):
    """Response model from agents."""
    success: bool
    data: dict[str, Any] | None = None
    message: str | None = None
    error: str | None = None


@copilot_app.post("/process-file", response_model=AgentResponse)
async def process_file(
    file: UploadFile = File(...),
    agent_type: str = Form(...)
):
    """
    Process an uploaded file using the appropriate agent.
    This is a direct API endpoint (not through CopilotKit chat).
    
    Args:
        file: Uploaded file (Excel, Word, or PDF)
        agent_type: "rota" or "unit"
        
    Returns:
        Extracted data and suggestions for form filling
    """
    try:
        file_content = await file.read()
        file_name = file.filename or "uploaded_file"
        
        if agent_type == "rota":
            result = await rota_agent.process_file_and_respond(
                file_content=file_content,
                file_name=file_name
            )
        elif agent_type == "unit":
            result = await unit_agent.process_file_and_respond(
                file_content=file_content,
                file_name=file_name
            )
        else:
            return AgentResponse(
                success=False,
                error=f"Unknown agent type: {agent_type}"
            )
        
        return AgentResponse(
            success=True,
            data=result,
            message=result.get("summary", "File processed successfully")
        )
        
    except Exception as e:
        return AgentResponse(
            success=False,
            error=str(e)
        )
