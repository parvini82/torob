"""
Workflow v2 - Clean, Modular, Multi-Provider AI Orchestration System.

A complete refactor of the workflow system with proper OOP design,
multi-provider model support, and robust state management.

Example usage:
    from src.service.workflow_v2 import create_scenario_runner

    runner = create_scenario_runner()
    results = runner.run_scenario("scenario_one", "https://example.com/image.jpg")

    # Or use convenience functions
    from src.service.workflow_v2 import run_scenario_from_url

    results = run_scenario_from_url("scenario_two", "https://example.com/image.jpg")
"""

# Import main classes and functions
from .main import (
    ScenarioRunner,
    create_scenario_runner,
    run_scenario_from_url,
    run_scenario_from_bytes
)

# Import core components
from .core import (
    StateManager,
    BaseNode,
    GraphBuilder,
    WorkflowLogger,
    get_workflow_logger
)

# Import model client
from .model_client import (
    ModelClient,
    create_model_client,
    Provider,
    ModelClientError,
    ProviderError
)

# Import configuration
from .config import (
    WorkflowConfig,
    ModelConfig,
    get_config
)

# Import scenarios for direct access
from .scenarios import (
    ScenarioOne,
    ScenarioTwo,
    ScenarioThree,
    ScenarioFour
)

# Import all nodes for advanced usage
from .nodes import (
    CaptionGeneratorNode,
    TagExtractorNode,
    ImageTagExtractorNode,
    TranslatorNode,
    MergerNode,
    RefinerNode,
    ConversationRefinerNode
)

__version__ = "2.0.0"

# Main exports for common usage
__all__ = [
    # Main runner and convenience functions
    "ScenarioRunner",
    "create_scenario_runner",
    "run_scenario_from_url",
    "run_scenario_from_bytes",

    # Core components
    "StateManager",
    "BaseNode",
    "GraphBuilder",
    "WorkflowLogger",
    "get_workflow_logger",

    # Model client
    "ModelClient",
    "create_model_client",
    "Provider",
    "ModelClientError",
    "ProviderError",

    # Configuration
    "WorkflowConfig",
    "ModelConfig",
    "get_config",

    # Scenarios (for direct instantiation)
    "ScenarioOne",
    "ScenarioTwo",
    "ScenarioThree",
    "ScenarioFour",

    # Nodes (for custom workflows)
    "CaptionGeneratorNode",
    "TagExtractorNode",
    "ImageTagExtractorNode",
    "TranslatorNode",
    "MergerNode",
    "RefinerNode",
    "ConversationRefinerNode"
]

# Version info
__author__ = "Workflow v2 Team"
__description__ = "Clean, modular AI orchestration system with multi-provider support"
