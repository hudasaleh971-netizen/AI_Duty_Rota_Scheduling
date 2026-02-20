"""
FastAPI endpoint for Nurse Scheduling API

Exposes the 3-agent CrewAI pipeline to the frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
import uvicorn


from src.crew import run_scheduling_crew

app = FastAPI(
    title="Nurse Scheduling API",
    description="AI-powered nurse scheduling using LLM-driven multi-agent reasoning",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Response Models
# ============================================================================

class ScheduleAssignment(BaseModel):
    date: str
    employeeId: str
    employeeName: str
    shiftCode: str


class EmployeeHoursDetail(BaseModel):
    total: float
    target: float
    balance: float

class ScheduleSummary(BaseModel):
    totalShifts: int
    assignedShifts: int
    unassignedShifts: int = 0
    # Support both simple float (legacy) and detailed object
    employeeHours: Dict[str, Union[float, EmployeeHoursDetail]]


class ScheduleResponse(BaseModel):
    status: str
    score: Optional[str] = None
    schedule: Optional[List[ScheduleAssignment]] = None
    summary: Optional[ScheduleSummary] = None
    error: Optional[str] = None
    details: Optional[str] = None


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "Nurse Scheduling API",
        "status": "running",
        "endpoints": {
            "POST /api/schedule/{rota_id}": "Generate optimized schedule for a rota",
            "GET /api/health": "Health check"
        }
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy"}


@app.post("/api/schedule/{rota_id}", response_model=ScheduleResponse)
async def generate_schedule(rota_id: str):
    """
    Generate an optimized schedule for the given rota.
    
    This runs the 3-agent LLM-driven pipeline:
    1. Requirements Analyzer: Interprets raw data into structured requirements
    2. Schedule Generator: Creates schedule using ReAct reasoning
    3. Schedule Critic: Validates and approves/rejects with feedback loop
    
    Args:
        rota_id: The rota configuration ID from the frontend
        
    Returns:
        ScheduleResponse with optimized schedule or error
    """
    try:
        # CrewAI Flow's kickoff() internally calls asyncio.run(), which conflicts
        # with uvicorn's running event loop. Offload to a thread pool to avoid
        # "asyncio.run() cannot be called from a running event loop" error.
        import asyncio
        result = await asyncio.to_thread(run_scheduling_crew, rota_id)
        
        return ScheduleResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Function moved to src.persistence



# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=5000,
        reload=True
    )
