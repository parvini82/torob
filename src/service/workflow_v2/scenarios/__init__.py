"""
Workflow scenarios for the v2 system.

This package contains scenario implementations that compose nodes
into complete workflow graphs for different use cases.
"""

from .scenario_zero import ScenarioZero
from .scenario_two import ScenarioTwo
from .scenario_one import ScenarioOne
from .scenario_three import ScenarioThree
from .scenario_four import ScenarioFour

__all__ = [
    "ScenarioZero",
    "ScenarioOne",
    "ScenarioTwo",
    "ScenarioThree",
    "ScenarioFour"
]
