import json
from datetime import datetime, date
from timefold.solver import SolverFactory
from domain import ShiftSchedule, Employee, Shift, TimeSpan, ProblemConfig, HardConstraintConfig, SoftConstraintConfig, ConstraintConfiguration
from solver import get_solver_config

def run_solver():
    # Load input data
    with open("generated/input_data.json", "r") as f:
        data = json.load(f)

    # Parse Employees
    employee_map = {}
    employee_list = []
    for emp_data in data["employees"]:
        unavailable_time_spans = [TimeSpan(**ts) for ts in emp_data.get("unavailableTimeSpans", [])]
        preferred_time_spans = [TimeSpan(**ts) for ts in emp_data.get("preferredTimeSpans", [])]
        
        employee = Employee(
            id=emp_data["id"],
            name=emp_data["name"],
            skills=emp_data["skills"],
            contractedHours=emp_data["contractedHours"],
            owingHours=emp_data["owingHours"],
            paidAbsenceHours=emp_data["paidAbsenceHours"],
            targetWorkingHours=emp_data["targetWorkingHours"],
            unavailableTimeSpans=unavailable_time_spans,
            preferredTimeSpans=preferred_time_spans,
            mentorId=emp_data["mentorId"]
        )
        employee_list.append(employee)
        employee_map[employee.id] = employee

    # Parse Shifts
    shift_map = {}
    shift_list = []
    for shift_data in data["shifts"]:
        shift = Shift(
            id=shift_data["id"],
            code=shift_data["code"],
            start=datetime.fromisoformat(shift_data["start"]),
            end=datetime.fromisoformat(shift_data["end"]),
            hours=shift_data["hours"],
            employee=None # Will be assigned by solver or lockedAssignments
        )
        shift_list.append(shift)
        shift_map[shift.id] = shift

    # Apply locked assignments
    for locked_assignment in data.get("lockedAssignments", []):
        employee_id = locked_assignment["employeeId"]
        shift_date = locked_assignment["date"]
        shift_code = locked_assignment["shiftCode"]

        target_shift_id = f"{shift_date}-{shift_code}"

        employee = employee_map.get(employee_id)
        shift = shift_map.get(target_shift_id)

        if employee and shift:
            shift.employee = employee
        else:
            print(f"Warning: Could not find employee {employee_id} or shift {target_shift_id} for locked assignment.")

    # Parse ProblemConfig
    problem_configuration = ProblemConfig(**data.get("config", {}))

    # Parse ConstraintConfiguration
    hard_constraint_configs = [HardConstraintConfig(**hc) for hc in data["constraints"].get("hard", [])]
    soft_constraint_configs = [SoftConstraintConfig(**sc) for sc in data["constraints"].get("soft", [])]
    constraint_specification = ConstraintConfiguration(
        hard_constraints=hard_constraint_configs,
        soft_constraints=soft_constraint_configs
    )

    # Create ShiftSchedule problem
    shift_schedule = ShiftSchedule(
        employee_list=employee_list,
        shift_list=shift_list,
        problem_configuration=problem_configuration,
        constraint_specification=constraint_specification
    )

    # Configure and run the solver
    solver_config = get_solver_config()
    solver_factory = SolverFactory.create(solver_config)
    solver = solver_factory.build_solver()

    print("Solving Shift Schedule...")
    solution = solver.solve(shift_schedule)
    print("Solver finished.")

    # Print the best solution
    print("\n--- Solved Shift Schedule ---")
    if solution:
        for shift in solution.shift_list:
            employee_name = shift.employee.name if shift.employee else "Unassigned"
            print(f"Shift ID: {shift.id}, Start: {shift.start.strftime('%Y-%m-%d %H:%M')}, End: {shift.end.strftime('%Y-%m-%d %H:%M')}, Employee: {employee_name}")
        print(f"\nScore: {solution.score}")
    else:
        print("No solution found.")

if __name__ == "__main__":
    run_solver()