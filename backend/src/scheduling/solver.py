"""
Timefold Solver for Nurse Scheduling

Generic solver that reads input_data.json and runs optimization.
"""
import json
from pathlib import Path
from typing import Optional

from timefold.solver import SolverFactory
from timefold.solver.config import (
    SolverConfig,
    ScoreDirectorFactoryConfig,
    TerminationConfig
)

from .domain import Shift, ShiftSchedule
from .constraint_library import build_constraint_provider
from .json_utils import load_input_data, parse_schedule, format_output


def solve_from_file(input_file: str, time_limit_seconds: int = 30) -> dict:
    """
    Solve scheduling problem from input_data.json file.
    
    Args:
        input_file: Path to input_data.json
        time_limit_seconds: Solver time limit
        
    Returns:
        Frontend-ready JSON dict
    """
    # Load and parse input
    data = load_input_data(input_file)
    return solve_from_dict(data, time_limit_seconds)


def solve_from_dict(data: dict, time_limit_seconds: int = 30) -> dict:
    """
    Solve scheduling problem from input data dict.
    
    Args:
        data: Input data with employees, shifts, constraintConfig
        time_limit_seconds: Solver time limit
        
    Returns:
        Frontend-ready JSON dict
    """
    # Parse schedule
    schedule = parse_schedule(data)
    
    print(f"📊 Solving: {len(schedule.employees)} employees, {len(schedule.shifts)} shifts")
    
    # Build constraint provider from config
    constraint_config = data.get("constraintConfig", {
        "hard": [
            {"name": "one_shift_per_day"},
            {"name": "honor_unavailability"},
        ],
        "soft": [
            {"name": "balance_hours", "weight": 100},
        ]
    })
    
    constraint_provider = build_constraint_provider(constraint_config)
    
    # Configure solver
    solver_config = SolverConfig(
        solution_class=ShiftSchedule,
        entity_class_list=[Shift],
        score_director_factory_config=ScoreDirectorFactoryConfig(
            constraint_provider_function=constraint_provider
        ),
        termination_config=TerminationConfig(
            spent_limit=f"PT{time_limit_seconds}S"
        )
    )
    
    # Create and run solver
    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()
    
    print("🔄 Running Timefold solver...")
    solution = solver.solve(schedule)
    
    print(f"✅ Solved! Score: {solution.score}")
    
    # Format output
    return format_output(solution)


# Entry point for Agent 2
def run_solver(input_file: str = None, time_limit: int = 30) -> dict:
    """
    Run solver - entry point for Agent 2.
    
    Args:
        input_file: Path to input_data.json (default: generated/input_data.json)
        time_limit: Solver time limit in seconds
        
    Returns:
        Frontend-ready schedule JSON
    """
    if input_file is None:
        input_file = str(Path(__file__).parent / "input_data.json")
    
    print(f"📁 Loading: {input_file}")
    return solve_from_file(input_file, time_limit)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Timefold solver")
    parser.add_argument("--input", default="generated/input_data.json", help="Input JSON file")
    parser.add_argument("--time-limit", type=int, default=30, help="Time limit in seconds")
    parser.add_argument("--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    result = run_solver(args.input, args.time_limit)
    
    output_str = json.dumps(result, indent=2)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_str)
        print(f"Saved to: {args.output}")
    else:
        print(output_str)
