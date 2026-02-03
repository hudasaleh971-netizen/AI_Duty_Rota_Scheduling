"""
Static Domain Model for Nurse Scheduling

This file contains the Timefold domain classes that don't change per rota.
Only the input_data.json changes.

Updated for Timefold 1.24.0 Python API which uses:
- @planning_entity and @planning_solution decorators
- Annotated[Type, PlanningVariable] for planning variables
- Annotated[Type, PlanningId] for entity IDs
"""
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional, Any, Annotated

from timefold.solver.domain import (
    planning_entity, 
    planning_solution,
    PlanningId,
    PlanningVariable,
    ValueRangeProvider,
    PlanningEntityCollectionProperty,
    ProblemFactCollectionProperty,
    PlanningScore
)
from timefold.solver.score import HardSoftScore


@dataclass
class TimeSpan:
    """Time span for availability/unavailability."""
    start: datetime
    end: datetime

    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end)

    def overlaps(self, other_start: datetime, other_end: datetime) -> bool:
        return max(self.start, other_start) < min(self.end, other_end)


@dataclass
class Employee:
    """
    Problem fact - employee data (not modified by solver).
    """
    id: str
    name: str
    skills: List[str] = field(default_factory=list)
    contracted_hours: int = 160
    owing_hours: int = 0
    paid_absence_hours: int = 0
    target_working_hours: int = 160
    unavailable_time_spans: List[TimeSpan] = field(default_factory=list)
    preferred_time_spans: List[TimeSpan] = field(default_factory=list)
    mentor_id: Optional[str] = None

    def __post_init__(self):
        # Convert dicts to TimeSpan objects
        self.unavailable_time_spans = [
            TimeSpan(**ts) if isinstance(ts, dict) else ts 
            for ts in self.unavailable_time_spans
        ]
        self.preferred_time_spans = [
            TimeSpan(**ts) if isinstance(ts, dict) else ts 
            for ts in self.preferred_time_spans
        ]

    def is_unavailable(self, shift_start: datetime, shift_end: datetime) -> bool:
        return any(ts.overlaps(shift_start, shift_end) for ts in self.unavailable_time_spans)

    def has_preference(self, shift_start: datetime, shift_end: datetime) -> bool:
        return any(ts.overlaps(shift_start, shift_end) for ts in self.preferred_time_spans)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Employee):
            return NotImplemented
        return self.id == other.id


@planning_entity
@dataclass
class Shift:
    """
    Planning entity - the solver assigns an employee to each shift.
    Uses Annotated types for Timefold 1.24.0 API.
    """
    id: Annotated[str, PlanningId]
    code: str
    start: datetime
    end: datetime
    hours: int
    locked_employee_id: Optional[str] = None  # Pre-assigned (hard constraint)
    
    # Planning variable - this is what the solver optimizes
    employee: Annotated[Optional[Employee], PlanningVariable] = field(default=None)

    def __post_init__(self):
        if isinstance(self.start, str):
            self.start = datetime.fromisoformat(self.start)
        if isinstance(self.end, str):
            self.end = datetime.fromisoformat(self.end)

    def get_date(self) -> date:
        return self.start.date()

    def get_duration_hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600

    def is_night_shift(self) -> bool:
        """Check if this is a night shift (crosses midnight or starts late)."""
        return self.end.date() > self.start.date() or self.start.hour >= 22

    def is_morning_shift(self) -> bool:
        """Check if this starts in the morning."""
        return self.start.hour < 12

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Shift):
            return NotImplemented
        return self.id == other.id


@planning_solution
@dataclass
class ShiftSchedule:
    """
    Planning solution - contains all employees and shifts.
    Uses Annotated types for Timefold 1.24.0 API.
    """
    # Problem facts with value range for employee assignment
    employees: Annotated[List[Employee], ProblemFactCollectionProperty, ValueRangeProvider] = field(default_factory=list)
    
    # Planning entities (shifts to be assigned)
    shifts: Annotated[List[Shift], PlanningEntityCollectionProperty] = field(default_factory=list)
    
    # Configuration
    config: dict = field(default_factory=dict)
    constraint_config: dict = field(default_factory=dict)
    
    # Score
    score: Annotated[HardSoftScore, PlanningScore] = field(default=None)

    def get_min_nurses_per_shift(self) -> int:
        return self.config.get("minNursesPerShift", 1)

    def get_rest_hours_between_shifts(self) -> int:
        for c in self.constraint_config.get("hard", []):
            if c.get("name") == "no_night_then_morning":
                return c.get("restHours", 10)
        return 10

    def get_max_consecutive_night_shifts(self) -> int:
        for c in self.constraint_config.get("soft", []):
            if c.get("name") == "avoid_consecutive_nights":
                return c.get("maxConsecutive", 2)
        return 2
