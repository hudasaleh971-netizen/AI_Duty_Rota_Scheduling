"""
JSON Utilities for Nurse Scheduling

Parse input_data.json and format output for frontend.
"""
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from .domain import Employee, Shift, ShiftSchedule, TimeSpan


def load_input_data(file_path: str) -> dict:
    """Load input data from JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def parse_schedule(data: dict) -> ShiftSchedule:
    """
    Convert input JSON to ShiftSchedule domain objects.
    
    Args:
        data: Input JSON dict with employees, shifts, config, constraintConfig
        
    Returns:
        ShiftSchedule ready for solving
    """
    # Parse employees
    employees = []
    employee_lookup = {}
    
    for emp_data in data.get("employees", []):
        employee = Employee(
            id=emp_data["id"],
            name=emp_data.get("name", emp_data["id"]),
            skills=emp_data.get("skills", []),
            contracted_hours=emp_data.get("contractedHours", 160),
            owing_hours=emp_data.get("owingHours", 0),
            paid_absence_hours=emp_data.get("paidAbsenceHours", 0),
            target_working_hours=emp_data.get("targetWorkingHours", 160),
            unavailable_time_spans=emp_data.get("unavailableTimeSpans", []),
            preferred_time_spans=emp_data.get("preferredTimeSpans", []),
            mentor_id=emp_data.get("mentorId"),
        )
        employees.append(employee)
        employee_lookup[employee.id] = employee
    
    # Parse shifts
    shifts = []
    for shift_data in data.get("shifts", []):
        shift = Shift(
            id=shift_data["id"],
            code=shift_data.get("code", "M"),
            start=shift_data["start"],
            end=shift_data["end"],
            hours=shift_data.get("hours", 8),
            locked_employee_id=shift_data.get("lockedEmployeeId"),
        )
        
        # Pre-assign locked shifts
        if shift.locked_employee_id and shift.locked_employee_id in employee_lookup:
            shift.employee = employee_lookup[shift.locked_employee_id]
        
        shifts.append(shift)
    
    return ShiftSchedule(
        employees=employees,
        shifts=shifts,
        config=data.get("config", {}),
        constraint_config=data.get("constraintConfig", {})
    )


def format_output(schedule: ShiftSchedule) -> dict:
    """
    Format solved schedule for frontend.
    
    Args:
        schedule: Solved ShiftSchedule
        
    Returns:
        JSON dict for frontend
    """
    # Build schedule array
    schedule_list = []
    employee_hours = {}
    
    for shift in sorted(schedule.shifts, key=lambda s: (s.start, s.id)):
        if shift.employee:
            schedule_list.append({
                "date": shift.start.strftime("%Y-%m-%d"),
                "employeeId": shift.employee.id,
                "employeeName": shift.employee.name,
                "shiftCode": shift.code,
            })
            
            # Track hours
            if shift.employee.name not in employee_hours:
                employee_hours[shift.employee.name] = 0
            employee_hours[shift.employee.name] += shift.hours
    
    # Count assignments
    assigned = sum(1 for s in schedule.shifts if s.employee is not None)
    unassigned = len(schedule.shifts) - assigned
    
    return {
        "status": "success",
        "score": str(schedule.score) if schedule.score else "0hard/0soft",
        "schedule": schedule_list,
        "summary": {
            "totalShifts": len(schedule.shifts),
            "assignedShifts": assigned,
            "unassignedShifts": unassigned,
            "employeeHours": employee_hours,
        }
    }
