"""Test script for fixed solver"""
import os
import sys

# Ensure utf-8 output for windows console
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    print("Importing run_solver...")
    from src.scheduling import run_solver
    
    print("Running solver check (5s)...")
    result = run_solver(time_limit=5)
    
    print("\n" + "="*40)
    print(f"STATUS: {result.get('status')}")
    print(f"SCORE:  {result.get('score')}")
    print("="*40)
    
    summary = result.get('summary', {})
    print(f"Total Shifts:      {summary.get('totalShifts')}")
    print(f"Assigned Shifts:   {summary.get('assignedShifts')}")
    print(f"Unassigned Shifts: {summary.get('unassignedShifts')}")
    
except Exception as e:
    import traceback
    traceback.print_exc()
