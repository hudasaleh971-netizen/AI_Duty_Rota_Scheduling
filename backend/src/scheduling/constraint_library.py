"""
Constraint Library for Nurse Scheduling

All possible constraints are defined here as functions.
The constraint_config in input_data.json determines which ones are used.
"""
from datetime import timedelta
from typing import List, Callable

from timefold.solver.score import (
    constraint_provider,
    ConstraintFactory,
    Joiners,
    HardSoftScore,
    ConstraintCollectors
)

from .domain import Shift, Employee, ShiftSchedule


# =============================================================================
# HARD CONSTRAINTS
# =============================================================================

def one_shift_per_day(factory: ConstraintFactory, **kwargs):
    """An employee can only work one shift per day."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: s.employee is not None)
        .join(Shift,
              Joiners.equal(lambda s: s.employee),
              Joiners.equal(lambda s: s.start.date()),
              Joiners.less_than(lambda s: s.id))
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("One shift per day")
    )


def no_night_then_morning(factory: ConstraintFactory, rest_hours: int = 10, **kwargs):
    """Must have minimum rest hours between shifts."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: s.employee is not None and s.is_night_shift())
        .join(Shift,
              Joiners.equal(lambda s: s.employee),
              Joiners.less_than(lambda s: s.end, lambda s: s.start))
        .filter(lambda s1, s2: 
                s2.is_morning_shift() and 
                (s2.start - s1.end).total_seconds() / 3600 < rest_hours)
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("No night then morning")
    )


def honor_unavailability(factory: ConstraintFactory, **kwargs):
    """Employee must not be assigned during unavailable times."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: 
                s.employee is not None and 
                s.employee.is_unavailable(s.start, s.end))
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Honor unavailability")
    )


def honor_locked_assignments(factory: ConstraintFactory, **kwargs):
    """Pre-assigned (locked) shifts must keep their assignment."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: 
                s.locked_employee_id is not None and 
                (s.employee is None or s.employee.id != s.locked_employee_id))
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Honor locked assignments")
    )


def required_skill(factory: ConstraintFactory, **kwargs):
    """Employee must have required skill for the shift."""
    # Note: This requires shifts to have a required_skill field
    return (
        factory.for_each(Shift)
        .filter(lambda s: 
                hasattr(s, 'required_skill') and
                s.required_skill is not None and 
                s.employee is not None and
                s.required_skill not in s.employee.skills)
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("Required skill")
    )


# =============================================================================
# SOFT CONSTRAINTS
# =============================================================================

def balance_hours(factory: ConstraintFactory, weight: int = 100, **kwargs):
    """Penalize deviation from target working hours."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: s.employee is not None)
        .group_by(
            lambda s: s.employee,
            ConstraintCollectors.sum(lambda s: s.hours)
        )
        .penalize(
            HardSoftScore.ONE_SOFT,
            lambda emp, total_hours: abs(emp.target_working_hours - total_hours) * weight // 100
        )
        .as_constraint("Balance hours")
    )


def honor_preferences(factory: ConstraintFactory, weight: int = 50, **kwargs):
    """Reward assigning preferred time slots."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: 
                s.employee is not None and 
                s.employee.has_preference(s.start, s.end))
        .reward(HardSoftScore.ONE_SOFT, lambda s: weight)
        .as_constraint("Honor preferences")
    )


def avoid_consecutive_nights(factory: ConstraintFactory, weight: int = 50, max_consecutive: int = 2, **kwargs):
    """Penalize more than max_consecutive night shifts in a row."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: s.employee is not None and s.is_night_shift())
        .join(Shift,
              Joiners.equal(lambda s: s.employee),
              Joiners.equal(lambda s: s.start.date() + timedelta(days=1), lambda s: s.start.date()))
        .filter(lambda s1, s2: s2.is_night_shift())
        .penalize(HardSoftScore.ONE_SOFT, lambda s1, s2: weight)
        .as_constraint("Avoid consecutive nights")
    )


def fair_shift_distribution(factory: ConstraintFactory, weight: int = 30, **kwargs):
    """Penalize uneven distribution of shifts."""
    return (
        factory.for_each(Shift)
        .filter(lambda s: s.employee is not None)
        .group_by(
            lambda s: s.employee,
            ConstraintCollectors.count()
        )
        .penalize(
            HardSoftScore.ONE_SOFT,
            lambda emp, count: count * count * weight // 100
        )
        .as_constraint("Fair shift distribution")
    )


# =============================================================================
# CONSTRAINT LIBRARY REGISTRY
# =============================================================================

HARD_CONSTRAINTS = {
    "one_shift_per_day": one_shift_per_day,
    "no_night_then_morning": no_night_then_morning,
    "honor_unavailability": honor_unavailability,
    "honor_locked_assignments": honor_locked_assignments,
    "required_skill": required_skill,
}

SOFT_CONSTRAINTS = {
    "balance_hours": balance_hours,
    "honor_preferences": honor_preferences,
    "avoid_consecutive_nights": avoid_consecutive_nights,
    "fair_shift_distribution": fair_shift_distribution,
}


def build_constraint_provider(constraint_config: dict):
    """
    Build a constraint provider function based on config.
    
    Args:
        constraint_config: Dict with "hard" and "soft" constraint lists
        
    Returns:
        A constraint_provider decorated function
    """
    hard_list = constraint_config.get("hard", [])
    soft_list = constraint_config.get("soft", [])
    
    @constraint_provider
    def define_constraints(factory: ConstraintFactory):
        constraints = []
        
        # Add hard constraints
        for c in hard_list:
            name = c.get("name")
            if name in HARD_CONSTRAINTS:
                constraints.append(HARD_CONSTRAINTS[name](factory, **c))
        
        # Add soft constraints
        for c in soft_list:
            name = c.get("name")
            if name in SOFT_CONSTRAINTS:
                constraints.append(SOFT_CONSTRAINTS[name](factory, **c))
        
        return constraints
    
    return define_constraints
