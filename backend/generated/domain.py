from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional

from timefold.solver.domain import planning_entity, planning_variable, planning_solution, problem_fact


@dataclass
class TimeSpan:
    start: datetime
    end: datetime

    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end)

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        # Check for overlap: [start, end) and [other_start, other_end)
        return max(self.start, other_start) < min(self.end, other_end)


@problem_fact
@dataclass(frozen=True)  # Make Employee immutable for better performance as a problem fact
class Employee:
    id: str
    name: str
    skills: List[str]
    contractedHours: int
    owingHours: int
    paidAbsenceHours: int
    targetWorkingHours: int
    unavailableTimeSpans: List[TimeSpan] = field(default_factory=list)
    preferredTimeSpans: List[TimeSpan] = field(default_factory=list)
    mentorId: Optional[str] = None

    def __post_init__(self):
        # Convert dicts to TimeSpan objects if they are not already
        object.__setattr__(self, 'unavailableTimeSpans', [TimeSpan(**ts) if isinstance(ts, dict) else ts for ts in self.unavailableTimeSpans])
        object.__setattr__(self, 'preferredTimeSpans', [TimeSpan(**ts) if isinstance(ts, dict) else ts for ts in self.preferredTimeSpans])

    def is_unavailable(self, shift_start: datetime, shift_end: datetime) -> bool:
        return any(ts.overlaps(shift_start, shift_end) for ts in self.unavailableTimeSpans)

    def has_preference(self, shift_start: datetime, shift_end: datetime) -> bool:
        return any(ts.overlaps(shift_start, shift_end) for ts in self.preferredTimeSpans)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Employee):
            return NotImplemented
        return self.id == other.id


@planning_entity
@dataclass
class Shift:
    id: str
    code: str
    start: datetime
    end: datetime
    hours: int
    # Planning variable
    employee: Optional[Employee] = planning_variable(Employee, value_range_name="employeeRange")

    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end)

    def get_date(self) -> date:
        return self.start.date()

    def get_duration(self) -> timedelta:
        return self.end - self.start

    def is_night_shift(self) -> bool:
        # A shift is considered a night shift if it crosses midnight
        # or if it starts late and ends early next day.
        # For simplicity, if the end date is after the start date, it's a night shift.
        return self.end.date() > self.start.date() or self.start.hour >= 18 # Starts after 6 PM and ends next day, or just crosses midnight

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Shift):
            return NotImplemented
        return self.id == other.id


@planning_solution
@dataclass
class ShiftSchedule:
    employee_list: List[Employee]
    shift_list: List[Shift]
    problem_config: dict = field(default_factory=dict)
    constraint_config: dict = field(default_factory=dict)

    @problem_fact
    def get_employees(self) -> List[Employee]:
        return self.employee_list

    @problem_fact
    def get_shifts(self) -> List[Shift]:
        return self.shift_list

    @property
    def get_min_nurses_per_shift(self) -> int:
        return self.problem_config.get("minNursesPerShift", 1)

    def get_rest_hours_between_shifts(self) -> int:
        for hard_constraint in self.constraint_config.get('hard', []):
            if hard_constraint.get('name') == 'no_night_then_morning':
                return hard_constraint.get('restHours', 10)
        return 10  # Default if not specified

    def get_max_consecutive_night_shifts(self) -> int:
        for soft_constraint in self.constraint_config.get('soft', []):
            if soft_constraint.get('name') == 'avoid_consecutive_nights':
                return soft_constraint.get('maxConsecutive', 2)
        return 2  # Default if not specified

    @planning_variable.value_range(output_type=Employee)
    def get_employee_range(self) -> List[Employee]:
        return self.employee_list
