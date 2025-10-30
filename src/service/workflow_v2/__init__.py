"""
LangGraph v2 - Modular and Extensible Workflow System.

This package provides a flexible framework for building complex
image analysis workflows using modular nodes and graph structures.

Example usage:
    from .main import ScenarioRunner

    runner = ScenarioRunner()
    results = runner.run_scenario("scenario_one", image_url)
"""

from .main import ScenarioRunner
from .core import BaseNode, GraphBuilder, StateManager

__version__ = "2.0.0"
__all__ = ["ScenarioRunner", "BaseNode", "GraphBuilder", "StateManager"]
