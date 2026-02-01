"""
Main entry point - run the Nurse Scheduling Crew
"""
import argparse
from src.crew import run_scheduling_crew


def main():
    parser = argparse.ArgumentParser(description="AI Duty Rota Scheduling")
    parser.add_argument("--rota-id", required=True, help="Rota configuration ID")
    parser.add_argument("--output", help="Output file path")
    args = parser.parse_args()
    
    output = run_scheduling_crew(args.rota_id)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Saved to: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
