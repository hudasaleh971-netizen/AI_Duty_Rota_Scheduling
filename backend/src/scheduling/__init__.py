"""
Timefold Shift Scheduling Package

Static code for nurse scheduling optimization.
"""
import os

# Set JAVA_HOME before importing Timefold (requires JVM)
# This must be done before any timefold imports
if not os.environ.get("JAVA_HOME"):
    # Common Java installation paths on Windows
    java_paths = [
        r"C:\Program Files\Eclipse Adoptium\jdk-17.0.17.10-hotspot",
        r"C:\Program Files\Java\jdk-17",
        r"C:\Program Files\Eclipse Adoptium\jdk-17",
        r"C:\Program Files\Java\jdk-21",
        r"C:\Program Files\Eclipse Adoptium\jdk-21",
    ]
    for path in java_paths:
        if os.path.exists(path):
            os.environ["JAVA_HOME"] = path
            break

from .domain import Employee, Shift, ShiftSchedule, TimeSpan
from .solver import run_solver, solve_from_file, solve_from_dict
from .json_utils import parse_schedule, format_output

__all__ = [
    "Employee",
    "Shift", 
    "ShiftSchedule",
    "TimeSpan",
    "run_solver",
    "solve_from_file",
    "solve_from_dict",
    "parse_schedule",
    "format_output",
]
