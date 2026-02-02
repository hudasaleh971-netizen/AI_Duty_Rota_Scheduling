from datetime import datetime, date
from domain import ShiftSchedule, Shift, Employee, TimeSpan

def parse_json_input(json_data: dict) -> ShiftSchedule:
    """
    Parses the input JSON data into a ShiftSchedule object.
    """
    config = json_data["config"]
    problem_id = json_data["problemId"]
    unit_name = config["unitName"]
    start_date = datetime.fromisoformat(config["startDate"]).date()
    end_date = datetime.fromisoformat(config["endDate"]).date()
    min_nurses_per_shift = config["minNursesPerShift"]

    employees_data = json_data["employees"]
    shifts_data = json_data["shifts"]
    pairings_data = json_data.get("pairings", [])
    locked_assignments_data = json_data.get("lockedAssignments", [])

    employees = []
    for emp_data in employees_data:
        unavailable_time_spans = []
        for unavail_data in emp_data.get("unavailableTimeSpans", []):
            unavailable_time_spans.append(TimeSpan(
                start=datetime.fromisoformat(unavail_data["start"]),
                end=datetime.fromisoformat(unavail_data["end"]),
                reason=unavail_data.get("reason")
            ))
        
        preferred_time_spans = []
        for pref_data in emp_data.get("preferredTimeSpans", []):
            preferred_time_spans.append(TimeSpan(
                start=datetime.fromisoformat(pref_data["start"]),
                end=datetime.fromisoformat(pref_data["end"]),
                reason=pref_data.get("reason")
            ))

        employees.append(Employee(
            id=emp_data["id"],
            name=emp_data["name"],
            skills=emp_data.get("skills", []),
            contracted_hours=emp_data.get("contractedHours", 0.0),
            owing_hours=emp_data.get("owingHours", 0.0),
            paid_absence_hours=emp_data.get("paidAbsenceHours", 0.0),
            target_working_hours=emp_data.get("targetWorkingHours", 0.0),
            unavailable_time_spans=unavailable_time_spans,
            preferred_time_spans=preferred_time_spans,
            mentor_id=emp_data.get("mentorId")
        ))
    
    # Convert locked assignments to a more accessible structure (employee_id, date, shift_code)
    locked_assignments_map = {}
    for locked_assign in locked_assignments_data:
        emp_id = locked_assign["employeeId"]
        assign_date = datetime.fromisoformat(locked_assign["date"]).date() # Only date part
        shift_code = locked_assign["shiftCode"]
        if emp_id not in locked_assignments_map:
            locked_assignments_map[emp_id] = {}
        locked_assignments_map[emp_id][assign_date] = shift_code

    shifts = []
    for shift_data in shifts_data:
        shift_start = datetime.fromisoformat(shift_data["start"])
        shift_end = datetime.fromisoformat(shift_data["end"])
        
        assigned_employee = None
        # Check if this shift has a locked assignment
        for emp in employees:
            if emp.id in locked_assignments_map and shift_start.date() in locked_assignments_map[emp.id]:
                if locked_assignments_map[emp.id][shift_start.date()] == shift_data["code"]:
                    assigned_employee = emp
                    break

        shifts.append(Shift(
            id=shift_data["id"],
            code=shift_data["code"],
            start=shift_start,
            end=shift_end,
            hours=shift_data["hours"],
            employee=assigned_employee # Pre-assign if locked
        ))

    return ShiftSchedule(
        problem_id=problem_id,
        unit_name=unit_name,
        start_date=start_date,
        end_date=end_date,
        min_nurses_per_shift=min_nurses_per_shift,
        employees=employees,
        shifts=shifts,
        pairings=pairings_data # Keep raw pairing data for constraints to access
    )


def schedule_to_json(schedule: ShiftSchedule) -> dict:
    """
    Converts a ShiftSchedule object back into a JSON-compatible dictionary.
    """
    solution_shifts = []
    for shift in schedule.shifts:
        solution_shifts.append({
            "id": shift.id,
            "code": shift.code,
            "start": shift.start.isoformat(),
            "end": shift.end.isoformat(),
            "hours": shift.hours,
            "employeeId": shift.employee.id if shift.employee else None
        })
    
    return {
        "problemId": schedule.problem_id,
        "config": {
            "unitName": schedule.unit_name,
            "startDate": schedule.start_date.isoformat(),
            "endDate": schedule.end_date.isoformat(),
            "minNursesPerShift": schedule.min_nurses_per_shift,
        },
        "employees": [
            {
                "id": emp.id,
                "name": emp.name,
                "skills": emp.skills,
                "contractedHours": emp.contracted_hours,
                "owingHours": emp.owing_hours,
                "paidAbsenceHours": emp.paid_absence_hours,
                "targetWorkingHours": emp.target_working_hours,
                "unavailableTimeSpans": [
                    {
                        "start": ts.start.isoformat(),
                        "end": ts.end.isoformat(),
                        "reason": ts.reason
                    } for ts in emp.unavailable_time_spans
                ],
                "preferredTimeSpans": [
                    {
                        "start": ts.start.isoformat(),
                        "end": ts.end.isoformat(),
                        "reason": ts.reason
                    } for ts in emp.preferred_time_spans
                ],
                "mentorId": emp.mentor_id
            } for emp in schedule.employees
        ],
        "shifts": solution_shifts,
        "pairings": schedule.pairings,
        "score": str(schedule.score)
    }