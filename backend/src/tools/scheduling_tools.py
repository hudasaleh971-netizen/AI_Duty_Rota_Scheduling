"""
Timefold Solver Tool for CrewAI

Wraps the run_solver function from src/scheduling/ as a CrewAI tool.
Agent 2 uses this to execute the Timefold optimization.

This tool uses:
- src/scheduling/solver.py: run_solver() entry point
- src/scheduling/domain.py: Employee, Shift, ShiftSchedule classes
- src/scheduling/json_utils.py: parse_schedule(), format_output()
- src/scheduling/constraint_library.py: build_constraint_provider()

The solver reads input_data.json and returns frontend-ready schedule JSON.
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from src.scheduling import run_solver
from pathlib import Path


class SolverInput(BaseModel):
    """Input schema for the Timefold solver tool."""
    file_path: str = Field(
        ..., 
        description="The absolute path to the input_data.json file."
    )


class TimefoldSolverTool(BaseTool):
    """
    Executes the Timefold optimization solver on input_data.json.
    
    This tool runs the pre-built Timefold solver code and returns
    the optimized schedule.
    """
    name: str = "run_timefold_solver"
    description: str = (
        "Executes the Timefold optimization solver on a specific JSON input file "
        "and returns the calculated schedule. Use this AFTER creating input_data.json."
    )
    args_schema: Type[BaseModel] = SolverInput

    def _run(self, file_path: str) -> dict:
        """Run the Timefold solver on the input file."""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {
                    "status": "error", 
                    "error": f"Input file not found: {file_path}"
                }
            
            print(f"🔧 Tool: Running Timefold solver on {file_path}...")
            result = run_solver(file_path, time_limit=30)
            print(f"✅ Solver complete. Score: {result.get('score', 'N/A')}")
            return result
            
        except Exception as e:
            print(f"❌ Solver error: {e}")
            return {"status": "error", "error": str(e)}
