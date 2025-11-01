"""
Main execution interface for Workflow v2 scenarios.

Provides the ScenarioRunner class for executing different workflow scenarios
with proper logging, error handling, and result management.
"""

import logging
from typing import Dict, Any, Optional

from .core.logger import WorkflowLogger
from .scenarios import ScenarioZero, ScenarioOne, ScenarioTwo, ScenarioThree, ScenarioFour


class ScenarioRunner:
    """
    Main runner class for executing different workflow scenarios.

    Supports all four implemented scenarios with flexible configuration
    and comprehensive result reporting.
    """

    def __init__(self, logging_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the scenario runner.

        Args:
            logging_config: Optional logging configuration
        """
        # Initialize logging
        self._setup_logging(logging_config or {})

        self.scenarios = {
            "scenario_one": ScenarioOne,
            "scenario_two": ScenarioTwo,
            "scenario_three": ScenarioThree,
            "scenario_four": ScenarioFour,
            "scenario_zero": ScenarioZero,
        }

        self.logger = logging.getLogger(f"{__name__}.ScenarioRunner")
        self.logger.info("ScenarioRunner initialized with 5 available scenarios")

    def _setup_logging(self, logging_config: Dict[str, Any]) -> None:
        """Setup logging configuration."""
        workflow_logger = WorkflowLogger()
        workflow_logger.configure_logging(
            level=logging_config.get("level", "INFO"),
            format_style=logging_config.get("format_style", "detailed"),
            enable_file_logging=logging_config.get("enable_file_logging", False),
            log_file_path=logging_config.get("log_file_path")
        )

    def run_scenario(
        self,
        scenario_name: str,
        image_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run a specific scenario.

        Args:
            scenario_name: Name of scenario to execute (scenario_one, scenario_two, etc.)
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
            raise ValueError(
                f"Unknown scenario: {scenario_name}. Available: {available}"
            )

        self.logger.info(f"Starting execution of {scenario_name}")
        self.logger.info(f"Image URL: {image_url[:50]}{'...' if len(image_url) > 50 else ''}")

        if config:
            self.logger.debug(f"Using custom configuration: {list(config.keys())}")

        try:
            # Create scenario instance
            scenario_class = self.scenarios[scenario_name]
            scenario_instance = scenario_class(config)

            # Execute scenario
            results = scenario_instance.execute(image_url)

            self.logger.info(f"Successfully completed {scenario_name}")
            self._log_results_summary(results)

            return results

        except Exception as e:
            self.logger.error(f"Error executing {scenario_name}: {str(e)}")
            raise

    def run_all_scenarios(
        self,
        image_url: str,
        configs: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
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
                    "execution_info": {
                        "scenario": scenario_name,
                        "success": False,
                        "error": str(e)
                    }
                }

        # Compile summary
        successful_scenarios = len([r for r in all_results.values() if "error" not in r])

        return {
            "image_url": image_url,
            "scenarios_run": len(all_results),
            "successful_scenarios": successful_scenarios,
            "failed_scenarios": len(all_results) - successful_scenarios,
            "results": all_results,
            "summary": self._create_comparison_summary(all_results)
        }

    def get_scenario_info(self, scenario_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get information about scenarios.

        Args:
            scenario_name: Optional specific scenario name

        Returns:
            Dictionary with scenario information
        """
        if scenario_name:
            if scenario_name not in self.scenarios:
                raise ValueError(f"Unknown scenario: {scenario_name}")

            scenario_class = self.scenarios[scenario_name]
            scenario_instance = scenario_class()
            return scenario_instance.get_scenario_info()

        # Return info for all scenarios
        all_info = {}
        for name, scenario_class in self.scenarios.items():
            scenario_instance = scenario_class()
            all_info[name] = scenario_instance.get_scenario_info()

        return all_info

    def _log_results_summary(self, results: Dict[str, Any]) -> None:
        """Log a summary of execution results."""
        scenario = results.get("scenario", "unknown")
        exec_info = results.get("execution_info", {})

        self.logger.info(f"Results summary for {scenario}:")

        # Log execution info
        if exec_info.get("success"):
            nodes_executed = exec_info.get("nodes_executed", [])
            self.logger.info(f"  Nodes executed: {len(nodes_executed)}")

            # Log scenario-specific metrics
            if scenario == "scenario_three":
                num_extractors = exec_info.get("parallel_extractors_used", 0)
                self.logger.info(f"  Parallel extractors: {num_extractors}")

            elif scenario == "scenario_four":
                iterations = exec_info.get("refinement_iterations", 0)
                converged = exec_info.get("converged_early", False)
                self.logger.info(f"  Refinement iterations: {iterations}")
                self.logger.info(f"  Early convergence: {converged}")

        # Log entity counts
        entity_sources = ["merged_tags", "conversation_tags", "extracted_tags", "image_tags"]

        for source in entity_sources:
            if source in results:
                data = results[source]
                entities = len(data.get("entities", []))
                categories = len(data.get("categories", []))

                self.logger.info(f"  {source}: {entities} entities, {categories} categories")
                break

        # Log translation results
        translation_sources = ["persian_output", "target_language_output"]

        for source in translation_sources:
            if source in results:
                trans_data = results[source]
                trans_entities = len(trans_data.get("entities", []))
                self.logger.info(f"  Translation: {trans_entities} entities")
                break

        # Log any errors
        if "errors" in results and results["errors"]:
            error_count = len(results["errors"])
            self.logger.warning(f"  Execution completed with {error_count} errors")

    def _create_comparison_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create a comparison summary of all scenario results."""
        summary = {
            "execution_times": {},
            "entity_counts": {},
            "accuracy_indicators": {},
            "model_usage": {}
        }

        for scenario_name, results in all_results.items():
            if "error" in results:
                continue

            exec_info = results.get("execution_info", {})

            # Extract entity counts
            entity_sources = ["merged_tags", "conversation_tags", "extracted_tags", "image_tags"]
            entity_count = 0

            for source in entity_sources:
                if source in results:
                    entity_count = len(results[source].get("entities", []))
                    break

            summary["entity_counts"][scenario_name] = entity_count

            # Model usage
            nodes_executed = exec_info.get("nodes_executed", [])
            summary["model_usage"][scenario_name] = len(nodes_executed)

            # Scenario-specific metrics
            if scenario_name == "scenario_three":
                summary["accuracy_indicators"][scenario_name] = {
                    "parallel_extractors": exec_info.get("parallel_extractors_used", 0),
                    "type": "consensus_based"
                }
            elif scenario_name == "scenario_four":
                summary["accuracy_indicators"][scenario_name] = {
                    "refinement_iterations": exec_info.get("refinement_iterations", 0),
                    "converged_early": exec_info.get("converged_early", False),
                    "type": "iterative_improvement"
                }

        return summary


# Convenience functions for external usage
def create_scenario_runner(logging_config: Optional[Dict[str, Any]] = None) -> ScenarioRunner:
    """
    Create a ScenarioRunner instance.

    Args:
        logging_config: Optional logging configuration

    Returns:
        Configured ScenarioRunner instance
    """
    return ScenarioRunner(logging_config)


def run_scenario_from_url(
    scenario_name: str,
    image_url: str,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function to run scenario with image URL.

    Args:
        scenario_name: Name of scenario to execute
        image_url: Image URL
        config: Optional scenario configuration

    Returns:
        Scenario execution results
    """
    runner = create_scenario_runner()
    return runner.run_scenario(scenario_name, image_url, config)


def run_scenario_from_bytes(
    scenario_name: str,
    image_bytes: bytes,
    config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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

    return run_scenario_from_url(scenario_name, data_uri, config)
