"""
Debug script to diagnose scenario issues.
"""

from src.service.workflow_v2 import create_scenario_runner
import json


def debug_scenario_detailed(scenario_name: str):
    """Debug a single scenario in detail."""

    print(f"\n🔍 DEBUGGING {scenario_name.upper()}")
    print("=" * 60)

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    try:
        runner = create_scenario_runner()
        results = runner.run_scenario(scenario_name, example_URL)

        print(f"✅ {scenario_name} execution completed")

        # Show all top-level keys
        print(f"\n📋 TOP-LEVEL KEYS IN RESULTS:")
        for key in sorted(results.keys()):
            value_type = type(results[key]).__name__
            if isinstance(results[key], (dict, list)):
                length = len(results[key])
                print(f"   {key}: {value_type} (length: {length})")
            else:
                print(f"   {key}: {value_type} = {results[key]}")

        # Check execution info
        exec_info = results.get("execution_info", {})
        print(f"\n⚙️  EXECUTION INFO:")
        for key, value in exec_info.items():
            print(f"   {key}: {value}")

        # Check for extraction results
        extraction_keys = ["extracted_tags", "image_tags", "merged_tags", "conversation_tags", "refined_tags"]
        print(f"\n🏷️  EXTRACTION RESULTS:")

        found_extraction = False
        for key in extraction_keys:
            if key in results:
                found_extraction = True
                data = results[key]
                entities_count = len(data.get("entities", [])) if isinstance(data, dict) else 0
                categories_count = len(data.get("categories", [])) if isinstance(data, dict) else 0
                print(f"   ✅ {key}: {entities_count} entities, {categories_count} categories")

                # Show first few entities
                if isinstance(data, dict) and "entities" in data:
                    entities = data["entities"][:]  # First 3
                    for i, entity in enumerate(entities, 1):
                        name = entity.get("name", "Unknown")
                        if "values" in entity:
                            values = entity.get("values", [])
                            values_str = str(values[:]) if isinstance(values, list) else str(values)
                        else:
                            values_str = entity.get("type", "Unknown")
                        print(f"      {i}. {name}: {values_str}")
            else:
                print(f"   ❌ {key}: NOT FOUND")

        if not found_extraction:
            print(f"   ⚠️  NO EXTRACTION RESULTS FOUND!")

        # Check translation results
        translation_keys = ["persian_output", "target_language_output"]
        print(f"\n🌐 TRANSLATION RESULTS:")

        found_translation = False
        for key in translation_keys:
            if key in results:
                found_translation = True
                data = results[key]
                if isinstance(data, dict):
                    entities_count = len(data.get("entities", []))
                    print(f"   ✅ {key}: {entities_count} entities")

                    # Show first few translated entities
                    entities = data.get("entities", [])[:]
                    for i, entity in enumerate(entities, 1):
                        name = entity.get("name", "Unknown")
                        if "values" in entity:
                            values = entity.get("values", [])
                            values_str = str(values[:]) if isinstance(values, list) else str(values)
                        else:
                            values_str = entity.get("type", "Unknown")
                        print(f"      {i}. {name}: {values_str}")
                else:
                    print(f"   ⚠️  {key}: EXISTS but not a dict - {type(data)}")
            else:
                print(f"   ❌ {key}: NOT FOUND")

        if not found_translation:
            print(f"   ⚠️  NO TRANSLATION RESULTS FOUND!")

        # Check for errors
        if "errors" in results and results["errors"]:
            print(f"\n❌ ERRORS FOUND:")
            for i, error in enumerate(results["errors"], 1):
                print(f"   {i}. {error}")
        else:
            print(f"\n✅ NO ERRORS FOUND")

        return results

    except Exception as e:
        print(f"❌ {scenario_name} FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def debug_all_scenarios():
    """Debug all scenarios."""

    print("🚀 DEBUGGING ALL SCENARIOS")
    print("=" * 80)

    scenarios = [
        "scenario_zero",
        "scenario_one",
        "scenario_two",
        "scenario_three",
        "scenario_four"
    ]

    results_summary = {}

    for scenario_name in scenarios:
        try:
            result = debug_scenario_detailed(scenario_name)

            # Summary
            has_extraction = any(key in result for key in
                                 ["extracted_tags", "image_tags", "merged_tags", "conversation_tags",
                                  "refined_tags"]) if result else False
            has_translation = any(
                key in result for key in ["persian_output", "target_language_output"]) if result else False
            has_errors = bool(result.get("errors")) if result else True

            results_summary[scenario_name] = {
                "success": result is not None,
                "has_extraction": has_extraction,
                "has_translation": has_translation,
                "has_errors": has_errors
            }

        except Exception as e:
            results_summary[scenario_name] = {
                "success": False,
                "error": str(e)
            }

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL SUMMARY")
    print("=" * 80)

    print(f"{'Scenario':<15} {'Success':<8} {'Extraction':<12} {'Translation':<12} {'Errors':<8}")
    print("-" * 70)

    for scenario_name, summary in results_summary.items():
        success = "✅" if summary["success"] else "❌"
        extraction = "✅" if summary.get("has_extraction", False) else "❌"
        translation = "✅" if summary.get("has_translation", False) else "❌"
        errors = "❌" if summary.get("has_errors", False) else "✅"

        print(f"{scenario_name:<15} {success:<8} {extraction:<12} {translation:<12} {errors:<8}")


if __name__ == "__main__":
    # Debug specific scenario
    debug_scenario_detailed("scenario_zero")
    debug_scenario_detailed("scenario_one")
    debug_scenario_detailed("scenario_two")
    debug_scenario_detailed("scenario_three")
    debug_scenario_detailed("scenario_four")

    # Or debug all scenarios
    # debug_all_scenarios()
