"""
Test script for all four Workflow v2 scenarios.
Complete testing of the refactored workflow system.
"""

from src.service.workflow_v2 import create_scenario_runner, run_scenario_from_url
from src.service.workflow_v2 import ScenarioOne, ScenarioTwo, ScenarioThree, ScenarioFour
import json


def running_all_scenarios():
    """Test all four scenarios with the provided image."""

    # Your image URL
    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print("=== Testing Workflow v2 - All Scenarios ===\n")

    # Method 1: Using ScenarioRunner
    print("🔥 Method 1: Using ScenarioRunner")
    runner = create_scenario_runner()

    # Test each scenario
    scenarios = ["scenario_one", "scenario_two", "scenario_three", "scenario_four"]

    for scenario_name in scenarios:
        print(f"\n--- Testing {scenario_name} ---")
        try:
            results = runner.run_scenario(scenario_name, example_URL)

            # Print key results
            exec_info = results.get("execution_info", {})
            print(f"✅ {scenario_name}: {exec_info.get('success', False)}")

            if exec_info.get("success"):
                # Print entity counts
                for source in ["merged_tags", "conversation_tags", "extracted_tags", "image_tags"]:
                    if source in results:
                        entities = len(results[source].get("entities", []))
                        categories = len(results[source].get("categories", []))
                        print(f"   📊 {source}: {entities} entities, {categories} categories")
                        break

                # Print translation info
                for trans_source in ["persian_output", "target_language_output"]:
                    if trans_source in results:
                        trans_entities = len(results[trans_source].get("entities", []))
                        print(f"   🌐 Translation: {trans_entities} entities")
                        break

            if "errors" in results and results["errors"]:
                print(f"   ⚠️  Errors: {len(results['errors'])}")

        except Exception as e:
            print(f"❌ {scenario_name} failed: {str(e)}")

    # Method 2: Using convenience functions
    print(f"\n\n🚀 Method 2: Using convenience functions")

    for scenario_name in scenarios[:2]:  # Test first 2 with convenience function
        print(f"\n--- Testing {scenario_name} (convenience) ---")
        try:
            results = run_scenario_from_url(scenario_name, example_URL)
            exec_info = results.get("execution_info", {})
            print(f"✅ {scenario_name}: {exec_info.get('success', False)}")

        except Exception as e:
            print(f"❌ {scenario_name} failed: {str(e)}")

    # Method 3: Direct scenario instantiation
    print(f"\n\n⚡ Method 3: Direct scenario instantiation")

    scenario_classes = {
        "scenario_one": ScenarioOne,
        "scenario_two": ScenarioTwo,
        "scenario_three": ScenarioThree,
        "scenario_four": ScenarioFour
    }

    # Custom configs for each scenario
    configs = {
        "scenario_one": {
            "node_config": {
                "caption_model": "qwen/qwen2.5-vl-32b-instruct:free",
                "target_language": "Persian"
            }
        },
        "scenario_two": {
            "node_config": {
                "caption_model": "qwen/qwen2.5-vl-32b-instruct:free",
                "target_language": "Persian"
            }
        },
        "scenario_three": {
            "node_config": {
                "num_parallel_extractors": 2,
                "target_language": "Persian"
            }
        },
        "scenario_four": {
            "node_config": {
                "max_iterations": 2,
                "target_language": "Persian"
            }
        }
    }

    for scenario_name, scenario_class in scenario_classes.items():
        print(f"\n--- Testing {scenario_name} (direct) ---")
        try:
            config = configs.get(scenario_name, {})
            scenario = scenario_class(config)
            results = scenario.execute(example_URL)

            exec_info = results.get("execution_info", {})
            print(f"✅ {scenario_name}: {exec_info.get('success', False)}")

            # Scenario-specific info
            if scenario_name == "scenario_three":
                parallel_count = exec_info.get("parallel_extractors_used", 0)
                print(f"   🔄 Parallel extractors: {parallel_count}")

            elif scenario_name == "scenario_four":
                iterations = exec_info.get("refinement_iterations", 0)
                converged = exec_info.get("converged_early", False)
                print(f"   🔄 Iterations: {iterations}, Converged: {converged}")

        except Exception as e:
            print(f"❌ {scenario_name} failed: {str(e)}")

    # Method 4: Compare all scenarios
    print(f"\n\n📊 Method 4: Compare all scenarios")
    try:
        runner = create_scenario_runner()
        comparison_results = runner.run_all_scenarios(example_URL)

        print(f"Total scenarios: {comparison_results['scenarios_run']}")
        print(f"Successful: {comparison_results['successful_scenarios']}")
        print(f"Failed: {comparison_results['failed_scenarios']}")

        # Print comparison summary
        summary = comparison_results.get("summary", {})
        if "entity_counts" in summary:
            print("\n📈 Entity counts comparison:")
            for scenario, count in summary["entity_counts"].items():
                print(f"   {scenario}: {count} entities")

        if "model_usage" in summary:
            print("\n🤖 Model usage comparison:")
            for scenario, usage in summary["model_usage"].items():
                print(f"   {scenario}: {usage} model calls")

    except Exception as e:
        print(f"❌ Comparison failed: {str(e)}")

    # Method 5: Get scenario information
    print(f"\n\n📋 Method 5: Scenario information")
    try:
        runner = create_scenario_runner()
        scenario_info = runner.get_scenario_info()

        for scenario_name, info in scenario_info.items():
            print(f"\n{scenario_name}:")
            print(f"   Name: {info['name']}")
            print(f"   Description: {info['description']}")
            print(f"   Estimated time: {info['estimated_time']}")
            print(f"   Model calls: {info['model_calls']}")

    except Exception as e:
        print(f"❌ Info retrieval failed: {str(e)}")

    print(f"\n\n🎉 Testing completed!")


def running_single_scenario(scenario_name="scenario_one"):
    """Test a single scenario with detailed output."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print(f"=== Testing {scenario_name} in detail ===\n")

    try:
        runner = create_scenario_runner()
        results = runner.run_scenario(scenario_name, example_URL)

        # Print detailed results
        print("📋 Execution Info:")
        exec_info = results.get("execution_info", {})
        for key, value in exec_info.items():
            print(f"   {key}: {value}")

        print(f"\n📊 Results Summary:")

        # Find the main results
        result_sources = ["merged_tags", "conversation_tags", "extracted_tags", "image_tags"]
        for source in result_sources:
            if source in results:
                data = results[source]
                print(f"\n🔍 {source}:")

                entities = data.get("entities", [])
                print(f"   Entities ({len(entities)}):")
                for i, entity in enumerate(entities[:3]):  # Show first 3
                    name = entity.get("name", "Unknown")
                    entity_type = entity.get("type", "Unknown")
                    confidence = entity.get("confidence", 0)
                    print(f"     {i + 1}. {name} ({entity_type}) - {confidence:.2f}")

                categories = data.get("categories", [])
                print(f"   Categories ({len(categories)}):")
                for i, category in enumerate(categories[:3]):  # Show first 3
                    name = category.get("name", "Unknown")
                    confidence = category.get("confidence", 0)
                    print(f"     {i + 1}. {name} - {confidence:.2f}")

                break

        # Show translation results
        trans_sources = ["persian_output", "target_language_output"]
        for source in trans_sources:
            if source in results:
                trans_data = results[source]
                trans_entities = trans_data.get("entities", [])
                print(f"\n🌐 Translation ({len(trans_entities)} entities):")
                for i, entity in enumerate(trans_entities[:3]):
                    name = entity.get("name", "Unknown")
                    print(f"     {i + 1}. {name}")
                break

        # Show errors if any
        if "errors" in results and results["errors"]:
            print(f"\n⚠️  Errors ({len(results['errors'])}):")
            for i, error in enumerate(results["errors"][:3]):
                node = error.get("node", "Unknown")
                error_msg = error.get("error", "Unknown error")
                print(f"     {i + 1}. {node}: {error_msg}")

    except Exception as e:
        print(f"❌ Testing failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Run all tests
    running_all_scenarios()

    # Uncomment to test single scenario in detail
    # test_single_scenario("scenario_one")
