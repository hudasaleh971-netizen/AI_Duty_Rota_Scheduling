"""
2-Agent Nurse Scheduling Crew - CrewAI Class-Based Structure

Uses @CrewBase decorator pattern with:
- @before_kickoff: Fetches Supabase data before agents start
- YAML configs: Separates prompt engineering from code
- TimefoldSolverTool: Agent 2 runs solver then validates
- @after_kickoff: Optional post-processing

Pipeline:
1. @before_kickoff: Fetch data from Supabase → inject into inputs
2. Agent 1: Transform data → Save input_data.json
3. Agent 2: Run solver → Validate locked requests → Format non-clinical codes
"""
import os
import json
from pathlib import Path
from typing import Dict, Any

from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task, before_kickoff, after_kickoff
from supabase import create_client
from dotenv import load_dotenv

from src.tools.scheduling_tools import TimefoldSolverTool

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
    print("⚠️ Langfuse not installed")

# ==========================================================================
# PATHS
# ==========================================================================
SCHEDULING_PATH = Path(__file__).parent / "scheduling"
INPUT_DATA_FILE = SCHEDULING_PATH / "input_data.json"


@CrewBase
class NurseSchedulingCrew:
    """
    2-Agent Nurse Scheduling Crew
    
    Agent 1: Interprets Data → Generates Input JSON (input_data.json)
    Agent 2: Runs Solver → Validates → Formats Codes (AL, SL, O) → Final JSON
    """
    
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    def __init__(self):
        # Initialize Supabase client
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_KEY")
        )
        # Initialize LLM
        self.llm = LLM(
            model="vertex_ai/gemini-2.5-flash",
            project=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            timeout=360,
        )

    @before_kickoff
    def fetch_rota_data(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetches all necessary data from Supabase BEFORE the agents start.
        This populates the 'inputs' dictionary available to agents/tasks.
        """
        rota_id = inputs.get('rota_id')
        if not rota_id:
            raise ValueError("rota_id is required in inputs")

        print(f"\n📡 [Before Kickoff] Fetching data for Rota ID: {rota_id}")

        # 1. Fetch Rota Config
        rota_res = self.supabase.table("rotas_config").select("*").eq("id", rota_id).single().execute()
        if not rota_res.data:
            raise ValueError(f"Rota not found: {rota_id}")
        
        # 2. Fetch Unit Data
        unit_id = rota_res.data["unit_id"]
        unit_res = self.supabase.table("units").select("*").eq("id", unit_id).single().execute()
        if not unit_res.data:
            raise ValueError(f"Unit not found: {unit_id}")
        
        print(f"✅ Fetched: {len(unit_res.data.get('staff', []))} staff members")
        
        # 3. Structure data for the Agents (inject into inputs dict)
        inputs['rota_data'] = json.dumps(rota_res.data, default=str)
        inputs['unit_data'] = json.dumps(unit_res.data, default=str)
        # Agent 2 needs special_requests for validation
        inputs['special_requests'] = json.dumps(rota_res.data.get("special_requests", []), default=str)

        # Pass file path so agents know where to save/read
        inputs['input_file_path'] = str(INPUT_DATA_FILE)
        
        return inputs

    @after_kickoff
    def log_completion(self, result):
        """Log completion after crew finishes."""
        print(f"\n{'='*70}")
        print("✅ CREW COMPLETE")
        print(f"{'='*70}")
        return result

    @agent
    def data_interpreter(self) -> Agent:
        """Agent 1: Transforms data to input_data.json (no tools needed)."""
        return Agent(
            config=self.agents_config['data_interpreter'],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    @agent
    def validator(self) -> Agent:
        """Agent 2: Runs solver, validates, and formats the schedule."""
        return Agent(
            config=self.agents_config['validator'],
            tools=[TimefoldSolverTool()],
            llm=self.llm,
            verbose=True,
            allow_delegation=False
        )

    @task
    def generate_input_task(self) -> Task:
        """Task 1: Generate input_data.json from Supabase data."""
        return Task(
            config=self.tasks_config['generate_input_task'],
            output_file=str(INPUT_DATA_FILE)
        )

    @task
    def run_and_validate_task(self) -> Task:
        """Task 2: Run solver, validate, and format for frontend."""
        return Task(
            config=self.tasks_config['run_and_validate_task']
        )

    @crew
    def crew(self) -> Crew:
        """Create the crew with sequential process."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )


# ==========================================================================
# ENTRY POINT (for backwards compatibility with api.py)
# ==========================================================================

def run_scheduling_crew(rota_id: str) -> dict:
    """
    Run the nurse scheduling crew.
    
    This function maintains backwards compatibility with api.py.
    
    Args:
        rota_id: The rota configuration ID
        
    Returns:
        Schedule JSON for frontend
    """
    print(f"\n{'='*70}")
    print("🏥 NURSE SCHEDULING CREW (Class-Based)")
    print(f"{'='*70}")
    print(f"Rota ID: {rota_id}")
    print(f"Output: {INPUT_DATA_FILE}")
    
    max_attempts = 2
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")
        
        try:
            # Create crew and run with rota_id input
            inputs = {'rota_id': rota_id}
            result = NurseSchedulingCrew().crew().kickoff(inputs=inputs)
            
            # Parse result
            result_str = str(result)
            
            # Clean up markdown if present
            if "```json" in result_str:
                result_str = result_str.split("```json")[1].split("```")[0]
            elif "```" in result_str:
                result_str = result_str.split("```")[1].split("```")[0]
            
            parsed_result = json.loads(result_str.strip())
            
            # Check for validation issues
            validation_issues = parsed_result.get("summary", {}).get("validationIssues", [])
            
            if not validation_issues:
                print(f"\n✅ SCHEDULE COMPLETE - All validations passed")
                return parsed_result
            else:
                print(f"⚠️ Validation issues: {validation_issues}")
                if attempt < max_attempts:
                    print("Retrying...")
                    continue
                else:
                    return parsed_result
                    
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parse error: {e}")
            # Return raw result if can't parse
            return {"status": "error", "error": f"JSON parse error: {e}", "raw": str(result)}
            
        except Exception as e:
            print(f"❌ Error: {e}")
            if attempt >= max_attempts:
                return {"status": "error", "error": f"Scheduling failed: {str(e)}"}
    
    return {"status": "error", "error": f"Failed after {max_attempts} attempts"}


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
