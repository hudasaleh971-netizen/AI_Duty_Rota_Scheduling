"""
3-Agent Nurse Scheduling Crew - CrewAI + Timefold Optimization

Pipeline:
1. Agent 1 (Data Interpreter): Supabase → Timefold JSON
2. Agent 2 (Code Generator): JSON → Timefold Python code
3. Agent 3 (Executor): Python code → Optimized schedule for frontend
"""
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import FileReadTool, FileWriterTool
from src.tools.supabase_tool import FetchRotaDataTool
import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ==========================================================================
# LANGFUSE TRACING (must be initialized before CrewAI)
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

# Paths
SKILL_PATH = os.path.expanduser("~/.gemini/skills/timefold-shift-scheduling")
GENERATED_PATH = Path(__file__).parent.parent / "generated"
GENERATED_PATH.mkdir(exist_ok=True)


def create_scheduling_crew(rota_id: str) -> Crew:
    """
    Create the 3-agent nurse scheduling crew.
    """
    
    # Vertex AI LLM
    vertex_llm = LLM(
        model="vertex_ai/gemini-2.5-flash",
        project=os.getenv("GOOGLE_CLOUD_PROJECT"),
        location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
        timeout=360,                 
    )
    
    # ==========================================================================
    # TOOLS
    # ==========================================================================
    supabase_tool = FetchRotaDataTool()
    
    skill_reader = FileReadTool(
        file_path=os.path.join(SKILL_PATH, "SKILL.md"),
        description="Read the Timefold skill documentation for code patterns"
    )
    
    example_reader = FileReadTool(
        file_path=os.path.join(SKILL_PATH, "examples"),
        description="Read Timefold example code files"
    )
    
    code_writer = FileWriterTool(
        directory=str(GENERATED_PATH),
        description="Write generated Timefold code files"
    )
    
    # ==========================================================================
    # AGENT 1: DATA INTERPRETER
    # ==========================================================================
    data_interpreter = Agent(
        role="Senior Nurse Scheduling Expert & Data Analyst",
        goal=f"Analyze rota {rota_id} and produce a complete, standardized Timefold JSON specification",
        backstory="""You are a nurse scheduling expert with 20+ years experience who deeply 
understands healthcare workforce management AND Timefold optimization input format.

YOUR EXPERTISE:

1. SHIFT CODE INTERPRETATION:
   - WORKING SHIFTS (ex: M/E/N see the shift_codes table for exact codes): Assigned by solver, count toward hours
   - Hours Counted paidABSENCE (ex: AL/SL/TR): Pre-determined unavailability, count toward hours but NOT shifts
   - Hours Not Counted OFF (ex: DO, O, PH): Not counted, employee available if needed
   - Read the shift_codes table to get exact codes used in the rota and their times

2. HOURS CALCULATION:
   - targetHours = contractedHours + owingHours
   - paidAbsenceHours = sum of AL/SL/TR days × hours per day
   - targetWorkingHours = targetHours - paidAbsenceHours (what solver assigns)

3. IMPLICIT REQUIREMENT DETECTION:
   - "preceptor for X" → pairing constraint (work together)
   - "new hire, training" → needs senior supervision
   - "prefers morning" → soft preference for M shifts
   - You understand that people need rest of atleast 10 hours between shifts unless another number is provided in the json
   - You understand that people don't like to work for more than 3 consecutive nights 
   - "part-time" or "Unit manager" → may have specific day and hours patterns""",
        tools=[supabase_tool],
        llm=vertex_llm,
        verbose=True,
        allow_delegation=False,
    )
    
    # ==========================================================================
    # AGENT 2: CODE GENERATOR
    # ==========================================================================
    code_generator = Agent(
        role="Timefold Constraint Optimization Developer",
        goal="Generate production-ready Timefold Python code from the JSON specification",
        backstory="""You are a senior Python developer specializing in Timefold constraint optimization.

You read the Timefold skill documentation to understand:
- Domain modeling with @planning_entity and @planning_solution
- Constraint Streams API with penalize/reward
- Hard vs soft constraints
- Hours balancing and pairing constraints

Given a JSON specification, you generate:
1. domain.py - Employee, Shift, ShiftSchedule classes matching the data
2. constraints.py - All hard/soft constraints from the spec
3. solver.py - Solver configuration
4. run_solver.py - Main script that loads data and runs solver

You write clean, well-documented Python code following best practices.""",
        tools=[skill_reader, example_reader, code_writer],
        llm=vertex_llm,
        verbose=True,
        allow_delegation=False,
    )
    
    # ==========================================================================
    # AGENT 3: EXECUTOR
    # ==========================================================================
    executor = Agent(
        role="Timefold Code Execution Specialist",
        goal="Execute the generated Timefold solver and return an optimized schedule",
        backstory="""You are a code execution specialist who runs optimization code.

Your responsibilities:
1. Read the generated Python files
2. Execute the solver with the input data
3. Format the output for the frontend UI
4. Handle errors gracefully

Output format for frontend:
{
  "status": "success",
  "score": "0hard/-5soft",
  "schedule": [
    {"date": "2026-02-01", "employeeId": "s1", "employeeName": "Fatima", "shiftCode": "M"},
    ...
  ],
  "summary": {
    "totalShifts": 63,
    "assignedShifts": 63,
    "employeeHours": {"Fatima": 144, ...}
  }
}""",
        llm=vertex_llm,
        verbose=True,
        allow_delegation=False,
    )
    
    # ==========================================================================
    # TASK 1: INTERPRET DATA & GENERATE TIMEFOLD JSON
    # ==========================================================================
    interpret_data_task = Task(
        description=f"""
FETCH the scheduling data for rota_id: {rota_id} using the fetch_rota_data tool.

Analyze ALL data and produce standardized Timefold JSON.

═══════════════════════════════════════════════════════════════════
OUTPUT JSON SCHEMA (STRICT)
═══════════════════════════════════════════════════════════════════

{{
  "problemId": "rota-{rota_id}",
  "config": {{
    "unitName": "unit name from data",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD",
    "minNursesPerShift": 2
  }},
  
  "employees": [
    {{
      "id": "staff-uuid",
      "name": "Full Name",
      "skills": ["Level X", "type"],
      "contractedHours": 160,
      "owingHours": 8,
      "paidAbsenceHours": 24,
      "targetWorkingHours": 144,
      "unavailableTimeSpans": [
        {{"start": "ISO8601", "end": "ISO8601", "reason": "AL"}}
      ],
      "preferredTimeSpans": [],
      "mentorId": null
    }}
  ],
  
  "shifts": [
    {{
      "id": "2026-02-01-M",
      "code": "M",
      "start": "2026-02-01T07:00:00",
      "end": "2026-02-01T15:00:00",
      "hours": 8
    }}
  ],
  
  "pairings": [
    {{
      "traineeId": "s4",
      "mentorId": "s1",
      "reason": "Omar comment: preceptor is Fatima",
      "weight": 7
    }}
  ],
  
  "constraints": {{
    "hard": [
      {{"name": "one_shift_per_day", "description": "..."}},
      {{"name": "no_night_then_morning", "restHours": 10}},
      {{"name": "honor_unavailability"}},
      {{"name": "minimum_coverage", "value": 2}}
    ],
    "soft": [
      {{"name": "balance_hours", "weight": 10}},
      {{"name": "honor_preferences", "weight": 5}},
      {{"name": "pair_trainees", "weight": 7}},
      {{"name": "avoid_consecutive_nights", "maxConsecutive": 2, "weight": 8}}
    ]
  }},
  
  "lockedAssignments": [
    {{"employeeId": "...", "date": "2026-02-01", "shiftCode": "M"}}
  ]
}}

═══════════════════════════════════════════════════════════════════
CRITICAL REQUIREMENTS
═══════════════════════════════════════════════════════════════════

1. Read shift_codes to get ACTUAL times (don't assume 07:00-15:00)
2. Calculate targetWorkingHours = contractedHours + owingHours - paidAbsenceHours
3. AL/SL/TR and other non shift codes (see the shift_codes table) dates go to unavailableTimeSpans with reason
4. DETECT pairings from comments (critical for realistic scheduling)
5. Generate shifts for EVERY day in range (based on direct care shift_codes for example M, E, N  or M, N per day)
6. Output ONLY valid JSON - no explanatory text
""",
        expected_output="""Valid JSON matching the schema with:
- All employees with correct hours calculations
- All shifts for every day in the date range
- Detected pairings or other requirements from comments
- Hard and soft constraints 
- Locked assignments from special requests""",
        agent=data_interpreter,
    )
    
    # ==========================================================================
    # TASK 2: GENERATE TIMEFOLD CODE
    # ==========================================================================
    generate_code_task = Task(
        description="""
You receive a Timefold JSON specification from the previous agent.

1. READ the Timefold skill documentation to understand the patterns
2. READ the example files (domain.py, constraints.py, solver.py)
3. GENERATE custom code based on the JSON specification

Files to create in the generated/ directory:

A) domain.py
   - Employee class with exact fields from JSON
   - Shift class with planning_variable for employee
   - ShiftSchedule as planning_solution

B) constraints.py
   - Implement EACH hard constraint from JSON
   - Implement EACH soft constraint with correct weights
   - Include pairing constraints from the pairings array

C) solver.py
   - SolverConfig with termination (30 seconds default)
   - Load input data and run solver

D) input_data.json
   - The JSON from Agent 1, saved for solver

Use the FileWriterTool to save each file.
""",
        expected_output="""Four files written to generated/:
- domain.py (Employee, Shift, ShiftSchedule)
- constraints.py (all constraints from spec)
- solver.py (configured solver)
- input_data.json (input for solver)""",
        agent=code_generator,
        context=[interpret_data_task],
    )
    
    # ==========================================================================
    # TASK 3: EXECUTE SOLVER & FORMAT OUTPUT
    # ==========================================================================
    execute_solver_task = Task(
        description="""
The previous agent generated Timefold Python code in the generated/ directory.

1. READ the generated files (domain.py, constraints.py, solver.py, input_data.json)
2. UNDERSTAND the code structure
3. EXECUTE the solver using Python
4. TRANSFORM the output to frontend format

Output MUST be valid JSON in this exact format:
{
  "status": "success",
  "score": "0hard/-5soft",
  "schedule": [
    {"date": "2026-02-01", "employeeId": "s1", "employeeName": "Fatima", "shiftCode": "M"},
    {"date": "2026-02-01", "employeeId": "s2", "employeeName": "Ahmed", "shiftCode": "E"},
    ...
  ],
  "summary": {
    "totalShifts": 63,
    "assignedShifts": 63,
    "unassignedShifts": 0,
    "employeeHours": {
      "Fatima Hassan": 144,
      "Ahmed Ali": 160
    }
  }
}

If there's an error, output:
{
  "status": "error",
  "error": "Error message",
  "details": "Stack trace or details"
}
""",
        expected_output="""JSON object with:
- status: "success" or "error"
- schedule: array of assignments (date, employeeId, employeeName, shiftCode)
- summary: statistics about the solution""",
        agent=executor,
        context=[generate_code_task],
    )
    
    # ==========================================================================
    # CREATE CREW
    # ==========================================================================
    crew = Crew(
        agents=[data_interpreter, code_generator, executor],
        tasks=[interpret_data_task, generate_code_task, execute_solver_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


def run_scheduling_crew(rota_id: str, agent_only: int = None) -> dict:
    """
    Run the nurse scheduling crew.
    
    Args:
        rota_id: The rota configuration ID
        agent_only: If set, run only up to this agent (1, 2, or 3)
        
    Returns:
        Schedule JSON for frontend
    """
    print(f"\n{'='*70}")
    print("🏥 3-AGENT NURSE SCHEDULING CREW")
    print(f"{'='*70}")
    print(f"Rota ID: {rota_id}")
    print(f"Agents: Data Interpreter → Code Generator → Executor")
    print(f"Output Dir: {GENERATED_PATH}")
    
    crew = create_scheduling_crew(rota_id)
    result = crew.kickoff()
    
    print(f"\n{'='*70}")
    print("✅ CREW COMPLETE")
    print(f"{'='*70}")
    
    # Parse the output - may be wrapped in markdown code blocks
    output_str = str(result)
    
    # Strip markdown code blocks if present
    if "```json" in output_str:
        # Extract JSON from markdown code block
        import re
        match = re.search(r'```json\s*([\s\S]*?)\s*```', output_str)
        if match:
            output_str = match.group(1).strip()
    elif "```" in output_str:
        # Try generic code block
        import re
        match = re.search(r'```\s*([\s\S]*?)\s*```', output_str)
        if match:
            output_str = match.group(1).strip()
    
    # Try to parse as JSON
    try:
        return json.loads(output_str)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"Raw output (first 500 chars): {output_str[:500]}")
        return {
            "status": "error",
            "error": "Failed to parse output as JSON",
            "details": str(e),
            "raw_output": output_str[:2000]  # Limit size for frontend
        }



if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run 3-Agent Nurse Scheduling Crew")
    parser.add_argument("--rota-id", required=True, help="Rota configuration ID")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--agent", type=int, choices=[1, 2, 3], help="Run only up to this agent")
    args = parser.parse_args()
    
    result = run_scheduling_crew(args.rota_id, agent_only=args.agent)
    
    output_str = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output_str)
        print(f"Saved to: {args.output}")
    else:
        print("\n--- SCHEDULE OUTPUT ---")
        print(output_str)
