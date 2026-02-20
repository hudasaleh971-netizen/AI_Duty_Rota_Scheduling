"""
LLM-Driven Nurse Scheduling — CrewAI Class-Based Architecture

3 sequential agents:
  1. data_analyzer         → Interpret raw data into structured requirements
  2. schedule_generator    → Generate schedule (reasoning=True for self-critique)
  3. final_validator       → Validate format + constraints, output Pydantic model

Hooks:
  @before_kickoff  → Fetch data from Supabase
  @after_kickoff   → Save schedule to Supabase
"""
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai_tools import FileReadTool
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ==========================================================================
# LANGFUSE TRACING
# ==========================================================================
try:
    from langfuse import get_client
    from openinference.instrumentation.crewai import CrewAIInstrumentor

    langfuse = get_client()
    if langfuse.auth_check():
        print("✅ Langfuse tracing enabled")
        CrewAIInstrumentor().instrument(skip_dep_check=True)
    else:
        print("⚠️ Langfuse auth failed - tracing disabled")
except ImportError:
    print("⚠️ Langfuse not installed - run: pip install langfuse openinference-instrumentation-crewai")

# ==========================================================================
# PATHS & LLM
# ==========================================================================
GENERATED_PATH = Path(__file__).parent.parent / "generated"
GENERATED_PATH.mkdir(exist_ok=True)

VERTEX_LLM = LLM(
    model="vertex_ai/gemini-2.5-flash",
    project=os.getenv("GOOGLE_CLOUD_PROJECT"),
    location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
    timeout=360,
)


# ==========================================================================
# PYDANTIC OUTPUT MODELS (matches Supabase + frontend contract)
# ==========================================================================
class ScheduleAssignment(BaseModel):
    """One shift assignment — maps directly to schedule_assignments table."""
    date: str = Field(description="Date in YYYY-MM-DD format")
    employeeId: str = Field(description="Staff ID (e.g. 's1')")
    employeeName: str = Field(description="Staff full name")
    shiftCode: str = Field(description="Shift code (D, N, O, AL, SL, PH, CL, TR, AD)")


class EmployeeHoursSummary(BaseModel):
    """Hours breakdown per employee."""
    total: float = Field(description="Total assigned hours")
    target: float = Field(description="Target hours for the period")
    balance: float = Field(description="Difference: total - target")


class ScheduleSummary(BaseModel):
    """Aggregate schedule statistics."""
    totalShifts: int = Field(description="Count of D + N entries")
    assignedShifts: int = Field(description="Count of all assigned shifts")
    unassignedShifts: int = Field(default=0)
    employeeHours: dict[str, EmployeeHoursSummary] = Field(
        description="Hours breakdown keyed by employee name"
    )


class ScheduleOutput(BaseModel):
    """Final structured output — used as output_pydantic on the validator task."""
    status: str = Field(default="success", description="'success' or 'partial'")
    schedule: list[ScheduleAssignment] = Field(
        description="Complete list of shift assignments"
    )
    summary: ScheduleSummary = Field(
        description="Aggregate statistics about the schedule"
    )
    validation_notes: list[str] = Field(
        default_factory=list,
        description="Notes from validation (passed checks, warnings)"
    )


# ==========================================================================
# CREW
# ==========================================================================
@CrewBase
class NurseSchedulingCrew:
    """
    3-agent sequential crew for nurse duty rota scheduling.

    Agent 1: Data Analyzer — interprets raw data into requirements model
    Agent 2: Schedule Generator — builds schedule with reasoning (self-critique)
    Agent 3: Final Validator — validates and outputs ScheduleOutput
    """

    agents: List[BaseAgent]
    tasks: List[Task]

    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    # Store rota_id for use in after_kickoff
    _rota_id: str = ""

    # ------------------------------------------------------------------
    # HOOKS
    # ------------------------------------------------------------------
    @before_kickoff
    def fetch_data(self, inputs):
        """Fetch rota + unit data from Supabase and inject into inputs."""
        rota_id = inputs.get("rota_id", "")
        self._rota_id = rota_id

        print(f"\n{'='*70}")
        print("🏥 NURSE SCHEDULING CREW (Class-Based + Reasoning)")
        print(f"{'='*70}")
        print(f"📥 Fetching data for rota {rota_id}...")

        from src.tools.supabase_tool import get_client
        client = get_client()

        rota = client.table("rotas_config").select("*").eq("id", rota_id).single().execute()
        if not rota.data:
            raise ValueError(f"Rota {rota_id} not found")

        unit_id = rota.data['unit_id']
        unit = client.table("units").select("*").eq("id", unit_id).single().execute()

        raw_data = {"rota": rota.data, "unit": unit.data}

        # Save to file (for validator to read as source of truth)
        raw_file = GENERATED_PATH / "raw_rota_data.json"
        with open(raw_file, "w") as f:
            json.dump(raw_data, f, indent=2, default=str)

        inputs["raw_data"] = json.dumps(raw_data, indent=2, default=str)
        print(f"💾 Raw data saved to {raw_file}")

        return inputs

    @after_kickoff
    def save_to_supabase(self, output):
        """Parse the crew output and persist to Supabase."""
        print(f"\n💾 Saving schedule to Supabase...")

        try:
            # Get schedule data from the Pydantic output
            if output.pydantic:
                schedule_data = output.pydantic.model_dump()
            else:
                schedule_data = json.loads(output.raw)

            schedule = schedule_data.get("schedule", [])

            if schedule:
                from src.tools.supabase_tool import save_schedule_direct
                save_schedule_direct(self._rota_id, schedule_data)
                print(f"✅ Saved {len(schedule)} assignments to database")
            else:
                print("⚠️ No schedule entries to save")

        except Exception as e:
            print(f"⚠️ DB save error: {e}")

        return output

    # ------------------------------------------------------------------
    # AGENTS
    # ------------------------------------------------------------------
    @agent
    def data_analyzer(self) -> Agent:
        return Agent(
            config=self.agents_config['data_analyzer'],  # type: ignore[index]
            llm=VERTEX_LLM,
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def schedule_generator(self) -> Agent:
        return Agent(
            config=self.agents_config['schedule_generator'],  # type: ignore[index]
            llm=VERTEX_LLM,
            verbose=True,
            allow_delegation=False,
            reasoning=True,
            max_reasoning_attempts=4,
        )

    @agent
    def final_validator(self) -> Agent:
        return Agent(
            config=self.agents_config['final_validator'],  # type: ignore[index]
            llm=VERTEX_LLM,
            verbose=True,
            allow_delegation=False,
            tools=[FileReadTool(file_path=str(GENERATED_PATH / "raw_rota_data.json"))],
        )

    # ------------------------------------------------------------------
    # TASKS
    # ------------------------------------------------------------------
    @task
    def analyze_requirements_task(self) -> Task:
        return Task(
            config=self.tasks_config['analyze_requirements_task'],  # type: ignore[index]
        )

    @task
    def generate_schedule_task(self) -> Task:
        return Task(
            config=self.tasks_config['generate_schedule_task'],  # type: ignore[index]
        )

    @task
    def validate_schedule_task(self) -> Task:
        return Task(
            config=self.tasks_config['validate_schedule_task'],  # type: ignore[index]
            output_pydantic=ScheduleOutput,
        )

    # ------------------------------------------------------------------
    # CREW
    # ------------------------------------------------------------------
    @crew
    def crew(self) -> Crew:
        """Assemble the 3-agent sequential crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


# ==========================================================================
# PUBLIC API (called by api.py)
# ==========================================================================
def run_scheduling_crew(rota_id: str) -> dict:
    """
    Run the nurse scheduling crew.
    Called by the FastAPI endpoint.
    """
    scheduling_crew = NurseSchedulingCrew()
    result = scheduling_crew.crew().kickoff(inputs={"rota_id": rota_id})

    # Prefer Pydantic-parsed output
    if result.pydantic:
        response = result.pydantic.model_dump()
    else:
        # Fallback: parse raw JSON
        try:
            response = json.loads(result.raw)
        except (json.JSONDecodeError, TypeError):
            response = {
                "status": "partial",
                "schedule": [],
                "summary": {
                    "totalShifts": 0,
                    "assignedShifts": 0,
                    "unassignedShifts": 0,
                    "employeeHours": {},
                },
                "validation_notes": [f"Raw output could not be parsed: {str(result.raw)[:200]}"],
            }

    print(f"\n{'='*70}")
    print(f"✅ SCHEDULING COMPLETE ({response.get('status', 'unknown')})")
    print(f"   Schedule entries: {len(response.get('schedule', []))}")
    print(f"{'='*70}")

    return response


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run Nurse Scheduling Crew")
    parser.add_argument("--rota-id", required=True, help="Rota configuration ID")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()

    result = run_scheduling_crew(args.rota_id)

    output_str = json.dumps(result, indent=2)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(f"Saved to: {args.output}")
    else:
        print("\n--- SCHEDULE OUTPUT ---")
        print(output_str)
