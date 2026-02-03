"""
FastAPI endpoint for Nurse Scheduling API

Exposes the 3-agent CrewAI pipeline to the frontend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn

# CrewAI scheduling with Timefold (requires Java 17+)
from src.crew import run_scheduling_crew

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
            "POST /api/schedule/{rota_id}": "Generate optimized schedule for a rota",
            "POST /api/schedule": "Generate schedule (rota_id in body)",
            "GET /api/health": "Health check"
        }
    }


@app.get("/api/health")
async def health():
    return {"status": "healthy", "scheduling": "enabled", "solver": "timefold"}


@app.post("/api/schedule/{rota_id}", response_model=ScheduleResponse)
async def generate_schedule(rota_id: str):
    """
    Generate an optimized schedule for the given rota.
    
    Uses CrewAI agents with Timefold solver for constraint optimization.
    """
    try:
        result = run_scheduling_crew(rota_id)
        return ScheduleResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/schedule", response_model=ScheduleResponse)
async def generate_schedule_body(request: ScheduleRequest):
    """
    Alternative endpoint accepting rota_id in request body.
    """
    try:
        result = run_scheduling_crew(request.rota_id)
        return ScheduleResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
