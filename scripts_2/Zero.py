"""
Updated test script including Scenario Zero.
"""
from fsspec.asyn import running_async

from src.service.workflow_v2 import create_scenario_runner, run_scenario_from_url
from src.service.workflow_v2 import ScenarioZero, ScenarioOne
import time


def running_scenario_zero():
    """Test the new ultra-fast Scenario Zero."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print("=== Testing Scenario Zero - Ultra-Fast ===\n")

    # Method 1: Using runner
    print("🚀 Method 1: Using ScenarioRunner")
    start_time = time.time()

    runner = create_scenario_runner()
    results = runner.run_scenario("scenario_zero", example_URL)

    execution_time = time.time() - start_time

    exec_info = results.get("execution_info", {})
    print(f"✅ Scenario Zero: {exec_info.get('success', False)}")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")
    print(f"🤖 Model calls: {exec_info.get('model_calls', 0)}")

    # Show results
    if "image_tags" in results:
        entities = len(results["image_tags"].get("entities", []))
        print(f"📊 Direct image analysis: {entities} entities")

    if "persian_output" in results:
        persian_entities = len(results["persian_output"].get("entities", []))
        print(f"🌐 Persian translation: {persian_entities} entities")

    # Method 2: Using convenience function
    print(f"\n⚡ Method 2: Using convenience function")
    start_time = time.time()

    results2 = run_scenario_from_url("scenario_zero", example_URL)
    execution_time2 = time.time() - start_time

    print(f"✅ Convenience function: {results2.get('execution_info', {}).get('success', False)}")
    print(f"⏱️  Execution time: {execution_time2:.2f} seconds")

    # Method 3: Direct instantiation
    print(f"\n💫 Method 3: Direct instantiation with custom config")

    config = {
        "node_config": {
            "target_language": "Persian",
            "image_model": None,  # Use env variable
            "translation_model": None  # Use env variable
        }
    }

    start_time = time.time()
    scenario = ScenarioZero(config)
    results3 = scenario.execute(example_URL)
    execution_time3 = time.time() - start_time

    print(f"✅ Direct instantiation: {results3.get('execution_info', {}).get('success', False)}")
    print(f"⏱️  Execution time: {execution_time3:.2f} seconds")


def compare_all_scenarios():
    """Compare all 5 scenarios including the new Scenario Zero."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print("=== Comparing All 5 Scenarios ===\n")

    scenarios = ["scenario_zero", "scenario_one", "scenario_two", "scenario_three", "scenario_four"]
    runner = create_scenario_runner()

    results_comparison = {}

    for scenario_name in scenarios:
        print(f"🔄 Testing {scenario_name}...")
        start_time = time.time()

        try:
            results = runner.run_scenario(scenario_name, example_URL)
            execution_time = time.time() - start_time

            exec_info = results.get("execution_info", {})

            results_comparison[scenario_name] = {
                "success": exec_info.get("success", False),
                "execution_time": execution_time,
                "model_calls": exec_info.get("model_calls", "unknown"),
                "entities_count": 0,
                "has_errors": "errors" in results and len(results["errors"]) > 0
            }

            # Find entity count
            for source in ["merged_tags", "conversation_tags", "image_tags", "extracted_tags"]:
                if source in results:
                    results_comparison[scenario_name]["entities_count"] = len(results[source].get("entities", []))
                    break

            print(
                f"✅ {scenario_name}: {execution_time:.1f}s, {results_comparison[scenario_name]['entities_count']} entities")

        except Exception as e:
            results_comparison[scenario_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ {scenario_name}: FAILED - {str(e)[:50]}...")

    # Print comparison table
    print(f"\n📊 SCENARIOS COMPARISON:")
    print(f"{'Scenario':<15} {'Success':<8} {'Time':<8} {'Models':<8} {'Entities':<10}")
    print("-" * 55)

    for scenario_name, data in results_comparison.items():
        if data.get("success"):
            time_str = f"{data['execution_time']:.1f}s"
            models_str = str(data.get('model_calls', '?'))
            entities_str = str(data.get('entities_count', '?'))
        else:
            time_str = "FAILED"
            models_str = "-"
            entities_str = "-"

        success_str = "✅" if data.get("success") else "❌"
        print(f"{scenario_name:<15} {success_str:<8} {time_str:<8} {models_str:<8} {entities_str:<10}")

    # Speed ranking
    successful_scenarios = {k: v for k, v in results_comparison.items() if v.get("success")}
    if successful_scenarios:
        sorted_by_speed = sorted(successful_scenarios.items(), key=lambda x: x[1]['execution_time'])

        print(f"\n🏆 SPEED RANKING:")
        for i, (scenario_name, data) in enumerate(sorted_by_speed, 1):
            print(f"{i}. {scenario_name}: {data['execution_time']:.1f}s")


if __name__ == "__main__":
    # Test Scenario Zero specifically
    running_scenario_zero()

    # Compare all scenarios
    print("\n" + "=" * 60 + "\n")
    compare_all_scenarios()
