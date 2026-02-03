"""
FastAPI endpoint for Nurse Scheduling API

Exposes the 3-agent CrewAI pipeline to the frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# TEMPORARILY DISABLED - Requires Java 17+ for Timefold
# from src.crew import run_scheduling_crew
from src.copilot_endpoint import copilot_app

app = FastAPI(
    title="Nurse Scheduling API",
    description="AI-powered nurse scheduling using CrewAI + Timefold",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000", "http://localhost:5173", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount CopilotKit agent endpoint
app.mount("/copilotkit", copilot_app)


# ============================================================================
# Response Models
# ============================================================================

class ScheduleAssignment(BaseModel):
    date: str
    employeeId: str
    employeeName: str
    shiftCode: str


class ScheduleSummary(BaseModel):
    totalShifts: int
    assignedShifts: int
    unassignedShifts: int = 0
    employeeHours: Dict[str, float]


class ScheduleResponse(BaseModel):
    status: str
    score: Optional[str] = None
    schedule: Optional[List[ScheduleAssignment]] = None
    summary: Optional[ScheduleSummary] = None
    error: Optional[str] = None
    details: Optional[str] = None


class ScheduleRequest(BaseModel):
    rota_id: str
    time_limit_seconds: int = 30


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "Nurse Scheduling API",
        "status": "running",
        "endpoints": {
            "POST /api/schedule": "Generate optimized schedule for a rota (TEMPORARILY DISABLED)",
            "GET /api/health": "Health check",
            "POST /copilotkit/process-file": "Process files with AI agents"
        }
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "copilotkit": "enabled", "scheduling": "disabled (requires Java 17+)"}


@app.post("/api/schedule/{rota_id}", response_model=ScheduleResponse)
async def generate_schedule(rota_id: str):
    """
    Generate an optimized schedule for the given rota.
    
    TEMPORARILY DISABLED - Requires Java 17+ for Timefold solver.
    """
    # TEMPORARILY DISABLED - Uncomment when Java 17+ is installed
    # try:
    #     result = run_scheduling_crew(rota_id)
    #     return ScheduleResponse(**result)
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))
    
    return ScheduleResponse(
        status="disabled",
        error="Scheduling temporarily disabled - requires Java 17+ for Timefold solver",
        details="Install Java 17+ and uncomment the crew import to enable scheduling"
    )


@app.post("/api/schedule", response_model=ScheduleResponse)
async def generate_schedule_body(request: ScheduleRequest):
    """
    Alternative endpoint accepting rota_id in request body.
    
    TEMPORARILY DISABLED - Requires Java 17+ for Timefold solver.
    """
    return ScheduleResponse(
        status="disabled",
        error="Scheduling temporarily disabled - requires Java 17+ for Timefold solver",
        details="Install Java 17+ and uncomment the crew import to enable scheduling"
    )


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
