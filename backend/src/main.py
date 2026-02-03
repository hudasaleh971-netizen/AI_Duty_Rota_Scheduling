"""
Main entry point - run the Nurse Scheduling Crew

Usage:
    python -m src.main --rota-id <rota-uuid>
    python -m src.main --rota-id <rota-uuid> --output schedule.json
"""
import argparse
import json
import sys
from src.crew import NurseSchedulingCrew, run_scheduling_crew


def main():
    parser = argparse.ArgumentParser(description="AI Duty Rota Scheduling")
    parser.add_argument("--rota-id", required=True, help="Rota configuration ID from Supabase")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--direct", action="store_true", help="Use direct crew kickoff instead of wrapper")
    args = parser.parse_args()
    
    try:
        if args.direct:
            # Use the class-based crew directly
            print("Using direct crew kickoff...")
            inputs = {'rota_id': args.rota_id}
            result = NurseSchedulingCrew().crew().kickoff(inputs=inputs)
            output = str(result)
        else:
            # Use the wrapper function (with retry logic)
            result = run_scheduling_crew(args.rota_id)
            output = json.dumps(result, indent=2)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"\n✅ Saved to: {args.output}")
        else:
            print("\n" + "="*70)
            print("SCHEDULE OUTPUT")
            print("="*70)
            print(output)
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
