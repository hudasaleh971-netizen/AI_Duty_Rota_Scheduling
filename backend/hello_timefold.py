from typing import Annotated, List, Optional
from dataclasses import dataclass, field
from timefold.solver.domain import (
    planning_solution, planning_entity, 
    PlanningId, PlanningVariable, PlanningScore,
    ProblemFactCollectionProperty, ValueRangeProvider,
    PlanningEntityCollectionProperty
)
from timefold.solver.score import HardSoftScore, constraint_provider, ConstraintFactory
from timefold.solver.config import SolverConfig, ScoreDirectorFactoryConfig, TerminationConfig, Duration
from timefold.solver import SolverFactory
import logging
import sys
import os
import shutil
from pathlib import Path

# Ensure JAVA_HOME is set before importing timefold
if not os.environ.get("JAVA_HOME"):
    java_path = shutil.which("java")
    if java_path:
        # Resolve symlinks to get real path
        real_path = Path(java_path).resolve()
        # Usually .../bin/java.exe -> parent is bin, parent.parent is JAVA_HOME
        java_home = real_path.parent.parent
        os.environ["JAVA_HOME"] = str(java_home)
        print(f"Set JAVA_HOME to: {os.environ['JAVA_HOME']}")
    else:
        # Fallback for common Windows paths
        jdks = list(Path("C:/Program Files/Eclipse Adoptium").glob("jdk*"))
        if jdks:
            os.environ["JAVA_HOME"] = str(jdks[0])
            print(f"Found JDK at: {jdks[0]}")

@planning_entity
@dataclass
class Item:
    id: Annotated[str, PlanningId]
    # Reference the ValueRangeProvider by name implied by the Solution field? 
    # Or references the type str? Timefold usually allows referencing the type/field.
    # We'll use reference to the collection "values" if needed, 
    # but by default it finds value range providers returning 'str'
    value: Annotated[Optional[str], PlanningVariable] = field(default=None)

@planning_solution
@dataclass
class Solution:
    # Use 'value_range_provider' arg inside Annotated?
    # In older Timefold/OptaPy we used @value_range_provider on a getter.
    # With Annotated, it's typically Annotated[List[str], ProblemFactCollectionProperty, ValueRangeProvider]
    values: Annotated[List[str], ProblemFactCollectionProperty, ValueRangeProvider]
    
    items: Annotated[List[Item], PlanningEntityCollectionProperty]
    
    score: Annotated[HardSoftScore, PlanningScore] = field(default=None)

@constraint_provider
def my_constraints(factory: ConstraintFactory):
    return [
        factory.for_each(Item)
        .filter(lambda i: i.value is None)
        .penalize(HardSoftScore.ONE_HARD)
        .as_constraint("All assigned")
    ]

if __name__ == "__main__":
    try:
        print("Initializing data...")
        sol = Solution(
            values=["A", "B", "C"],
            items=[Item(id="1"), Item(id="2"), Item(id="3")]
        )

        print("Configuring solver...")
        config = SolverConfig(
            solution_class=Solution,
            entity_class_list=[Item],
            score_director_factory_config=ScoreDirectorFactoryConfig(
                constraint_provider_function=my_constraints
            ),
            termination_config=TerminationConfig(
                spent_limit=Duration(seconds=2)
            )
        )

        print("Building solver...")
        solver_factory = SolverFactory.create(config)
        solver = solver_factory.build_solver()

        print("Solving...")
        result = solver.solve(sol)
        
        print(f"DONE! Score: {result.score}")
        for item in result.items:
            print(f"Item {item.id} -> {item.value}")

    except Exception as e:
        import traceback
        traceback.print_exc()
