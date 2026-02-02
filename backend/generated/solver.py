from timefold.solver.config import SolverConfig, TerminationConfig
from constraints import get_score_constraints
from domain import ShiftSchedule

def get_solver_config() -> SolverConfig:
    return SolverConfig(solution_class=ShiftSchedule,
                        entity_class_list=[ShiftSchedule.get_shifts.__annotations__['return'].__args__[0]],
                        # Using `get_shifts.__annotations__['return'].__args__[0]` to get the type of elements in the list (Shift)
                        # Note: This is a bit of a workaround to get the entity class from the solution class method's return type.
                        # In a real scenario, you'd likely directly provide `Shift` if it's imported.
                        score_calculator_class=get_score_constraints,
                        termination_config=TerminationConfig(spent_limit= "PT30S")) # 30 seconds
