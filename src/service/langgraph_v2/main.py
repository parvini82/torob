"""
Main execution file for LangGraph v2 scenarios.

This module provides a unified interface for executing different
workflow scenarios with proper logging and error handling.
"""

import logging
import json
from typing import Dict, Any, Optional, Union
from .scenarios.scenario_one import ScenarioOne
from .scenarios.scenario_two import ScenarioTwo
from .scenarios.scenario_three import ScenarioThree
from .scenarios.scenario_four import ScenarioFour

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class ScenarioRunner:
    """
    Main runner class for executing different workflow scenarios.

    Supports all four implemented scenarios with flexible configuration
    and comprehensive result reporting.
    """

    def __init__(self):
        """Initialize the scenario runner."""
        self.scenarios = {
            "scenario_one": ScenarioOne,
            "scenario_two": ScenarioTwo,
            "scenario_three": ScenarioThree,
            "scenario_four": ScenarioFour
        }
        self.logger = logging.getLogger(__name__)

    def run_scenario(self, scenario_name: str, image_url: str,
                    config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Run a specific scenario.

        Args:
            scenario_name: Name of scenario to execute
            image_url: Image URL or data URI
            config: Optional configuration for the scenario

        Returns:
            Scenario execution results

        Raises:
            ValueError: If scenario name is not recognized
            Exception: If scenario execution fails
        """
        if scenario_name not in self.scenarios:
            available = list(self.scenarios.keys())
            raise ValueError(f"Unknown scenario: {scenario_name}. Available: {available}")

        self.logger.info(f"Starting execution of {scenario_name}")
        self.logger.info(f"Image URL: {image_url[:50]}{'...' if len(image_url) > 50 else ''}")

        try:
            scenario_class = self.scenarios[scenario_name]
            scenario_instance = scenario_class(config)
            results = scenario_instance.execute(image_url)

            self.logger.info(f"Successfully completed {scenario_name}")
            self._log_results_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing {scenario_name}: {str(e)}")
            raise

    def run_all_scenarios(self, image_url: str,
                         configs: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Run all available scenarios on the same image.

        Args:
            image_url: Image URL or data URI
            configs: Optional configurations per scenario

        Returns:
            Results from all scenarios
        """
        configs = configs or {}
        all_results = {}

        self.logger.info(f"Running all scenarios on image: {image_url[:50]}...")

        for scenario_name in self.scenarios.keys():
            try:
                scenario_config = configs.get(scenario_name, {})
                result = self.run_scenario(scenario_name, image_url, scenario_config)
                all_results[scenario_name] = result

            except Exception as e:
                self.logger.error(f"Failed to run {scenario_name}: {str(e)}")
                all_results[scenario_name] = {
                    "error": str(e),
                    "scenario": scenario_name,
                    "status": "failed"
                }

        return {
            "image_url": image_url,
            "scenarios_run": len(all_results),
            "successful_scenarios": len([r for r in all_results.values() if "error" not in r]),
            "results": all_results
        }

    def get_scenario_info(self) -> Dict[str, Any]:
        """
        Get information about all available scenarios.

        Returns:
            Dictionary with scenario descriptions and capabilities
        """
        return {
            "scenario_one": {
                "name": "Caption → Tags → Image Tags → Merge → Translate",
                "description": "Comprehensive workflow with both caption-based and direct image analysis",
                "nodes": ["CaptionGenerator", "TagExtractor", "ImageTagExtractor", "Merger", "Translator"],
                "use_case": "Most comprehensive analysis with multiple extraction methods"
            },
            "scenario_two": {
                "name": "Caption → Tags → Translate",
                "description": "Simple caption-based workflow",
                "nodes": ["CaptionGenerator", "TagExtractor", "Translator"],
                "use_case": "Fast and simple image analysis via caption generation"
            },
            "scenario_three": {
                "name": "Parallel Extractors → Merge → Translate",
                "description": "Parallel processing with multiple simultaneous extractors",
                "nodes": ["ParallelImageExtractors", "ParallelMerger", "Translator"],
                "use_case": "High-confidence results through parallel processing"
            },
            "scenario_four": {
                "name": "Extract → Iterative Refinement → Translate",
                "description": "Conversation loop with iterative tag refinement",
                "nodes": ["ImageTagExtractor", "ConversationRefiner", "Translator"],
                "use_case": "Highest accuracy through iterative improvement"
            }
        }

    def _log_results_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""
        scenario = results.get("scenario", "unknown")

        # Log English output summary
        english_output = results.get("english_output", {})
        english_entities = english_output.get("entities", [])

        # Log Persian output summary
        persian_output = results.get("persian_output", {})
        persian_entities = persian_output.get("entities", [])

        self.logger.info(f"Results summary for {scenario}:")
        self.logger.info(f"  English entities: {len(english_entities)}")
        self.logger.info(f"  Persian entities: {len(persian_entities)}")

        # Log scenario-specific metrics
        if scenario == "scenario_three":
            num_extractors = results.get("num_parallel_extractors", 0)
            self.logger.info(f"  Parallel extractors used: {num_extractors}")

        elif scenario == "scenario_four":
            convergence_info = results.get("convergence_info", {})
            iterations = convergence_info.get("iterations_used", 0)
            converged = convergence_info.get("converged_early", False)
            self.logger.info(f"  Refinement iterations: {iterations}")
            self.logger.info(f"  Converged early: {converged}")


def run_scenario_from_bytes(scenario_name: str, image_bytes: bytes,
                           config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to run scenario with image bytes.

    Args:
        scenario_name: Name of scenario to execute
        image_bytes: Raw image bytes
        config: Optional scenario configuration

    Returns:
        Scenario execution results
    """
    import base64

    # Convert bytes to data URI
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_uri = f"data:image/jpeg;base64,{b64}"

    runner = ScenarioRunner()
    return runner.run_scenario(scenario_name, data_uri, config)


def run_scenario_from_url(scenario_name: str, image_url: str,
                         config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to run scenario with image URL.

    Args:
        scenario_name: Name of scenario to execute
        image_url: Image URL
        config: Optional scenario configuration

    Returns:
        Scenario execution results
    """
    runner = ScenarioRunner()
    return runner.run_scenario(scenario_name, image_url, config)


def main():
    """
    Example usage and testing of the scenario runner.

    This function demonstrates how to use all scenarios with
    different configurations.
    """
    runner = ScenarioRunner()

    # Example image URL (replace with actual image)
    test_image_url = "https://example.com/product-image.jpg"

    print("=== LangGraph v2 Scenario Runner ===\\n")

    # Display available scenarios
    scenario_info = runner.get_scenario_info()
    print("Available Scenarios:")
    for name, info in scenario_info.items():
        print(f"  {name}: {info['description']}")
    print()

    # Example configurations for each scenario
    example_configs = {
        "scenario_one": {
            # Standard configuration for comprehensive analysis
        },
        "scenario_two": {
            # Fast processing configuration
        },
        "scenario_three": {
            "num_parallel_extractors": 3,
            "extractor_config": {
                "model": "google/gemini-flash-1.5"
            }
        },
        "scenario_four": {
            "max_iterations": 2,
            "refiner_config": {
                "model": "google/gemini-flash-1.5"
            }
        }
    }

    # Run individual scenarios
    for scenario_name in ["scenario_one", "scenario_two"]:
        try:
            print(f"\\n--- Running {scenario_name} ---")
            config = example_configs.get(scenario_name, {})
            results = runner.run_scenario(scenario_name, test_image_url, config)

            # Display key results
            english_entities = results.get("english_output", {}).get("entities", [])
            persian_entities = results.get("persian_output", {}).get("entities", [])

            print(f"English entities found: {len(english_entities)}")
            print(f"Persian entities found: {len(persian_entities)}")

            # Show first few entities as example
            if english_entities:
                print(f"Example English entity: {english_entities[0]}")
            if persian_entities:
                print(f"Example Persian entity: {persian_entities[0]}")

        except Exception as e:
            print(f"Error running {scenario_name}: {e}")

    # Example of running all scenarios
    print("\\n--- Running All Scenarios ---")
    try:
        all_results = runner.run_all_scenarios(test_image_url, example_configs)
        print(f"Successfully ran {all_results['successful_scenarios']} out of {all_results['scenarios_run']} scenarios")

    except Exception as e:
        print(f"Error running all scenarios: {e}")


if __name__ == "__main__":
    main()