"""
Nurse Scheduling Crew - Expert Prompt for Timefold Optimization

This crew generates input for Timefold constraint solver. The agent must:
1. Understand the data deeply (staff, shifts, comments, relationships)
2. Generate proper Timefold-compatible JSON with employees, shifts, and constraints
3. Interpret implicit requirements from comments (e.g., "preceptor for X" = should work together)
"""
from crewai import Agent, Task, Crew, Process, LLM
from src.tools.supabase_tool import FetchRotaDataTool
import os
from dotenv import load_dotenv

load_dotenv()


def create_scheduling_crew(rota_id: str) -> Crew:
    """
    Create the nurse scheduling crew with expert-level prompt.
    """
    
    # Vertex AI LLM
    vertex_llm = LLM(
        model="vertex_ai/gemini-2.0-flash",
        project=os.getenv("VERTEX_PROJECT"),
        location=os.getenv("VERTEX_LOCATION", "us-central1"),
    )
    
    # Supabase tool
    supabase_tool = FetchRotaDataTool()
    
    # ========================================
    # EXPERT AGENT WITH DEEP UNDERSTANDING
    # ========================================
    scheduling_expert = Agent(
        role="Senior Nurse Scheduling Expert & Workforce Optimization Specialist",
        goal=f"Generate a complete, realistic Timefold optimization input for rota {rota_id} that captures all explicit AND implicit scheduling requirements",
        backstory="""You are BOTH a seasoned nurse scheduling expert (20+ years in healthcare) AND 
a constraint optimization specialist who deeply understands Timefold solver input format.

YOUR UNIQUE EXPERTISE:

1. NURSE SCHEDULING DOMAIN:
   - You understand hospital units have different shift patterns (M=Morning, E=Evening, N=Night)
   - You know that AL (Annual Leave), SL (Sick Leave), TR (Training), DO (Day Off) are NOT work shifts
     but they COUNT toward total hours for pay/balance purposes
   - You understand target hours = contracted hours + owing hours from previous month
   - You know owing hours carry forward if staff work more or less than target
   - You read between the lines in comments (e.g., "preceptor for X" means they should work TOGETHER)

2. TIMEFOLD OPTIMIZATION:
   - You produce JSON that Timefold can directly consume
   - You understand hard constraints (MUST be satisfied) vs soft constraints (SHOULD be optimized)
   - You model employee skills, availability, and unavailability correctly
   - You know shifts need ISO 8601 datetime format for start/end times

3. IMPLICIT REQUIREMENT DETECTION:
   - When a comment says "Omar is training" or "new hire, still in training" you pair them with senior staff
   - When someone "prefers morning shifts" you add that as a soft preference
   - When rules say "no back-to-back night shifts" you create a hard constraint
   - You infer mentorship relationships and shift pairing needs from context""",
        tools=[supabase_tool],
        llm=vertex_llm,
        verbose=True,
        allow_delegation=False,
    )
    
    # ========================================
    # TASK WITH COMPREHENSIVE INSTRUCTIONS
    # ========================================
    generate_timefold_task = Task(
        description=f"""
FETCH the scheduling data for rota_id: {rota_id} using the fetch_rota_data tool.

Then carefully analyze ALL the data and generate Timefold-compatible JSON.

═══════════════════════════════════════════════════════════════════
STEP 1: UNDERSTAND THE DATA
═══════════════════════════════════════════════════════════════════

A) EMPLOYEES (from staff array):
   - Each staff member has: id, name, position (Level 1/2/3), type, contractedHours
   - SKILLS = [position, type] (e.g., ["Level 2", "Direct Care"])
   - TARGET HOURS = contractedHours + owingHours (from staff_owing_hours)
   - READ THE COMMENTS CAREFULLY for hidden requirements:
     * "preceptor for X" → This person should work with X (pairing constraint)
     * "new hire, still in training" → Needs supervision, pair with senior
     * "prefers morning shifts" → Add preference for M shifts
     * "part-time" → May prefer specific days

B) SHIFTS (from shift_codes array):
   - WORKING SHIFTS: M (Morning 07:00-15:00), E (Evening 15:00-23:00), N (Night 23:00-07:00)
   - NON-WORKING CODES: DO (Day Off), AL (Annual Leave), SL (Sick Leave), TR (Training)
   - NON-WORKING codes count toward hours but are NOT shifts to assign!
   - Generate M/E/N shift SLOTS for every day in the date range

C) SPECIAL REQUESTS (pre-filled assignments):
   - isLocked=true → HARD CONSTRAINT (must honor exactly, employee unavailable for other shifts)
   - isLocked=false → SOFT PREFERENCE (try to honor but can change if needed)
   - If shiftCode is AL/SL/TR → Employee is UNAVAILABLE on that date

D) UNIT RULES:
   - Parse the rules string for constraints (e.g., "no back-to-back night shifts")
   - min_nurses_per_shift tells you minimum coverage

═══════════════════════════════════════════════════════════════════
STEP 2: GENERATE TIMEFOLD JSON
═══════════════════════════════════════════════════════════════════

{{
  "problemId": "rota-{rota_id}",
  "config": {{
    "unitName": "...",
    "scheduleName": "Month YYYY Rota",
    "startDate": "YYYY-MM-DD",
    "endDate": "YYYY-MM-DD"
  }},
  
  "employees": [
    {{
      "id": "staff-uuid",
      "name": "Nurse Name",
      "skills": ["Level 2", "Direct Care"],
      "contractedHours": 160,
      "targetHours": 148,
      "unavailableTimeSpans": [
        // From locked AL/SL/TR requests - employee cannot work these days
        {{"start": "2026-02-03T00:00:00", "end": "2026-02-03T23:59:59"}}
      ],
      "preferredTimeSpans": [
        // From comments like "prefers morning shifts"
      ],
      "unpreferredTimeSpans": [
        // From unlocked requests that are preferences
      ]
    }}
  ],
  
  "shifts": [
    {{
      "id": "2026-02-01-M",
      "start": "2026-02-01T07:00:00",
      "end": "2026-02-01T15:00:00",
      "hours": 8,
      "requiredSkills": [],  // optional, e.g., ["Level 2"] if specific skill needed
      "minEmployees": 2
    }}
  ],
  
  "constraints": {{
    "hard": [
      {{
        "name": "no_overlapping_shifts",
        "description": "Employee cannot work two shifts on the same day"
      }},
      {{
        "name": "no_night_then_morning",
        "description": "Cannot work Night shift then Morning shift next day (rest required)"
      }},
      {{
        "name": "honor_locked_requests",
        "description": "Locked assignments (isLocked=true) must be respected"
      }},
      {{
        "name": "minimum_coverage",
        "description": "Each shift must have at least X nurses",
        "value": 2
      }}
    ],
    "soft": [
      {{
        "name": "balance_hours_to_target",
        "description": "Distribute shifts so each employee gets close to their targetHours",
        "weight": 10
      }},
      {{
        "name": "honor_preferences",
        "description": "Try to assign employees their preferred shifts/times",
        "weight": 5
      }},
      {{
        "name": "avoid_3_consecutive_nights",
        "description": "Avoid assigning more than 2 consecutive night shifts",
        "weight": 8
      }},
      {{
        "name": "pair_trainees_with_mentors",
        "description": "New hires should work same shifts as their preceptor/mentor",
        "weight": 7,
        "pairs": [
          // DETECTED FROM COMMENTS - e.g., Omar's mentor is Fatima
          {{"trainee": "s4", "mentor": "s1"}}
        ]
      }}
    ]
  }},
  
  "lockedAssignments": [
    // From special_requests where isLocked=true AND shiftCode is M/E/N
    {{
      "employeeId": "...",
      "date": "2026-02-01",
      "shiftType": "M"
    }}
  ]
}}

═══════════════════════════════════════════════════════════════════
CRITICAL REQUIREMENTS
═══════════════════════════════════════════════════════════════════

1. Generate shifts for EVERY day from startDate to endDate (M, E, N each day)
2. Include ALL employees with correct target hours calculated
3. DETECT mentorship/pairing from comments - this is CRITICAL for realistic scheduling
4. Use ISO 8601 format for all datetime fields
5. AL/SL/TR go into unavailableTimeSpans, NOT into shift assignments
6. Target hours can be slightly over/under - difference goes to next month's owing
7. Output ONLY valid JSON - no explanatory text outside the JSON
""",
        expected_output="""A complete Timefold-compatible JSON object with:
- problemId and config
- employees array with skills, targetHours, and availability spans  
- shifts array for every M/E/N slot in the date range (with ISO 8601 times)
- constraints object with hard and soft constraints (including detected pairings)
- lockedAssignments from special requests

The JSON must capture ALL implicit requirements detected from staff comments.""",
        agent=scheduling_expert,
    )
    
    # Create crew
    crew = Crew(
        agents=[scheduling_expert],
        tasks=[generate_timefold_task],
        process=Process.sequential,
        verbose=True,
    )
    
    return crew


def run_scheduling_crew(rota_id: str) -> str:
    """
    Run the nurse scheduling crew.
    """
    print(f"\n{'='*70}")
    print("🏥 NURSE SCHEDULING EXPERT CREW (CrewAI + Vertex AI)")
    print(f"{'='*70}")
    print(f"Rota ID: {rota_id}")
    print("Generating Timefold optimization input...")
    
    crew = create_scheduling_crew(rota_id)
    result = crew.kickoff()
    
    print(f"\n{'='*70}")
    print("✅ CREW COMPLETE")
    print(f"{'='*70}")
    
    return str(result)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Nurse Scheduling Crew")
    parser.add_argument("--rota-id", required=True, help="Rota configuration ID")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()
    
    output = run_scheduling_crew(args.rota_id)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Saved to: {args.output}")
    else:
        print("\n--- TIMEFOLD INPUT ---")
        print(output)
