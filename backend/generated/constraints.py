from datetime import timedelta
from typing import List

from timefold.solver.constraint import ConstraintFactory, ConstraintStream
from timefold.solver.score import HardSoftScore

from domain import ShiftSchedule, Shift, Employee

def get_score_constraints(constraint_factory: ConstraintFactory, constraint_config: dict):
    hard_constraints = constraint_config.get("hard", [])
    soft_constraints = constraint_config.get("soft", [])

    constraints = []

    # Hard Constraints
    if any(c["name"] == "one_shift_per_day" for c in hard_constraints):
        constraints.append(one_shift_per_day(constraint_factory))
    if any(c["name"] == "no_night_then_morning" for c in hard_constraints):
        constraints.append(no_night_then_morning(constraint_factory))
    if any(c["name"] == "honor_unavailability" for c in hard_constraints):
        constraints.append(honor_unavailability(constraint_factory))
    if any(c["name"] == "minimum_coverage" for c in hard_constraints):
        constraints.append(minimum_coverage(constraint_factory))

    # Soft Constraints
    for soft_constraint in soft_constraints:
        if soft_constraint["name"] == "balance_hours":
            constraints.append(balance_hours(constraint_factory, soft_constraint["weight"]))
        elif soft_constraint["name"] == "honor_preferences":
            constraints.append(honor_preferences(constraint_factory, soft_constraint["weight"]))
        elif soft_constraint["name"] == "pair_trainees":
            constraints.append(pair_trainees(constraint_factory, soft_constraint["weight"]))
        elif soft_constraint["name"] == "avoid_consecutive_nights":
            constraints.append(avoid_consecutive_nights(constraint_factory, soft_constraint["weight"]))

    return constraints


# --- Hard Constraints ---

def one_shift_per_day(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each_unique_pair(Shift)
    .filter(lambda shift1, shift2: shift1.employee is not None
                                    and shift1.employee == shift2.employee
                                    and shift1.get_date() == shift2.get_date())
    .penalize("One shift per day", HardSoftScore.ONE_HARD)

def no_night_then_morning(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each(Shift)
        .if_exists(Shift,
                   lambda shift: shift.employee,
                   lambda shift: shift.is_night_shift(),
                   # Join with another shift for the same employee
                   constraint_factory.join_on(lambda shift1, shift2: shift1.employee == shift2.employee),
                   # The second shift must start after the first one ends
                   constraint_factory.join_on(lambda shift1, shift2: shift2.start >= shift1.end),
                   # The second shift must start within a specific window after the first one ends
                   # and the gap should be less than the required rest hours
                   constraint_factory.join_on(lambda shift1, shift2: shift2.start < (shift1.end + timedelta(hours=ShiftSchedule.get_rest_hours_between_shifts(None)))), # Pass None for static method call
                   # The second shift should not be a night shift if the first was a night shift (to avoid double counting issues)
                   constraint_factory.join_on(lambda shift1, shift2: not shift2.is_night_shift())
        )
        .penalize("No night then morning", HardSoftScore.ONE_HARD)

def honor_unavailability(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None
                               and shift.employee.is_unavailable(shift.start, shift.end))
        .penalize("Honor unavailability", HardSoftScore.ONE_HARD)

def minimum_coverage(constraint_factory: ConstraintFactory):
    return constraint_factory.for_each(Shift)
        .group_by(lambda shift: shift.id,
                  constraint_factory.count_distinct(lambda shift: shift.employee))
        .filter(lambda shift_id, num_employees: num_employees < ShiftSchedule.get_min_nurses_per_shift(None))
        .penalize("Minimum coverage", HardSoftScore.ONE_HARD, lambda shift_id, num_employees: ShiftSchedule.get_min_nurses_per_shift(None) - num_employees)

# --- Soft Constraints ---

def balance_hours(constraint_factory: ConstraintFactory, weight: int):
    # This is a simplified balance hours. A more complex one would consider target working hours.
    # For now, it penalizes deviations from an average, or simply rewards employees working their target hours.
    # Given the problem statement, we'll penalize deviation from targetWorkingHours.
    return constraint_factory.for_each(Employee)
        .join(Shift,
              constraint_factory.join_on(lambda employee, shift: employee == shift.employee))
        .group_by(lambda employee, shift: employee,
                  constraint_factory.sum(lambda employee, shift: shift.hours))
        .penalize("Balance hours", HardSoftScore.of_soft(weight),
                  lambda employee, total_hours_worked: abs(employee.targetWorkingHours - total_hours_worked))

def honor_preferences(constraint_factory: ConstraintFactory, weight: int):
    return constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None
                               and shift.employee.has_preference(shift.start, shift.end))
        .reward("Honor preferences", HardSoftScore.of_soft(weight))

def pair_trainees(constraint_factory: ConstraintFactory, weight: int):
    # Assuming 'mentorId' implies a mentor-trainee relationship.
    # This constraint rewards if a mentor and their mentee work together on overlapping shifts.
    return constraint_factory.for_each(Employee)
        .filter(lambda employee: employee.mentorId is not None)
        .join(Employee,
              constraint_factory.join_on(lambda employee, mentor: employee.mentorId == mentor.id))
        .join(Shift, 
              constraint_factory.join_on(lambda trainee, mentor, trainee_shift: trainee == trainee_shift.employee))
        .join(Shift, 
              constraint_factory.join_on(lambda trainee, mentor, trainee_shift, mentor_shift: mentor == mentor_shift.employee),
              constraint_factory.join_on(lambda trainee, mentor, trainee_shift, mentor_shift: 
                                         trainee_shift.overlaps(mentor_shift.start, mentor_shift.end)) # Assuming a method in Shift or TimeSpan
        )
        .reward("Pair trainees", HardSoftScore.of_soft(weight))

def avoid_consecutive_nights(constraint_factory: ConstraintFactory, weight: int):
    return constraint_factory.for_each(Shift)
        .filter(lambda shift: shift.employee is not None and shift.is_night_shift())
        .join(Shift,
              constraint_factory.join_on(lambda shift1, shift2: shift1.employee == shift2.employee),
              constraint_factory.join_on(lambda shift1, shift2: shift2.start == shift1.end + timedelta(hours=12)) # Assuming 12hr shifts back-to-back
        )
        .group_by(lambda shift1, shift2: shift1.employee,
                  constraint_factory.count())
        .filter(lambda employee, consecutive_nights: consecutive_nights > ShiftSchedule.get_max_consecutive_night_shifts(None))
        .penalize("Avoid consecutive nights", HardSoftScore.of_soft(weight),
                  lambda employee, consecutive_nights: consecutive_nights - ShiftSchedule.get_max_consecutive_night_shifts(None))

