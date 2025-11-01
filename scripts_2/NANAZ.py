"""
Clean and Beautiful Test Script for Workflow v2 Scenarios.
Displays fashion analysis results in a readable format.
"""

from src.service.workflow_v2 import create_scenario_runner
import json
from datetime import datetime
import time


class Colors:
    """ANSI color codes for beautiful terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(title: str, char: str = "="):
    """Print a beautiful header."""
    width = 80
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print(char * width)
    print(f"{title:^{width}}")
    print(char * width)
    print(f"{Colors.ENDC}")


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.CYAN}{Colors.BOLD}📋 {title}{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─' * (len(title) + 4)}{Colors.ENDC}")


def print_entity(entity: dict, index: int, max_name_length: int = 20):
    """Print a single entity in a beautiful format."""
    name = entity.get("name", "Unknown")

    # Handle both formats: new (name/values) and old (name/type)
    if "values" in entity:
        values = entity.get("values", [])
        if isinstance(values, list):
            display_values = ", ".join(values[:3])  # Show first 3 values
            if len(values) > 3:
                display_values += f" (+{len(values) - 3} more)"
        else:
            display_values = str(values)
        detail = f"Values: {display_values}"
    else:
        entity_type = entity.get("type", "Unknown")
        detail = f"Type: {entity_type}"

    confidence = entity.get("confidence", 0)

    # Truncate name if too long
    display_name = name[:max_name_length] + "..." if len(name) > max_name_length else name

    confidence_color = Colors.GREEN if confidence > 0.8 else Colors.YELLOW if confidence > 0.6 else Colors.RED

    print(f"   {Colors.BLUE}{index:2d}.{Colors.ENDC} {Colors.BOLD}{display_name:<{max_name_length}}{Colors.ENDC} "
          f"| {detail:<50} | {confidence_color}Conf: {confidence:.2f}{Colors.ENDC}")


def print_category(category: dict, index: int):
    """Print a single category in a beautiful format."""
    name = category.get("name", "Unknown")
    cat_type = category.get("type", category.get("level", "general"))
    confidence = category.get("confidence", 0)

    confidence_color = Colors.GREEN if confidence > 0.8 else Colors.YELLOW if confidence > 0.6 else Colors.RED

    print(f"   {Colors.BLUE}{index:2d}.{Colors.ENDC} {Colors.BOLD}{name:<30}{Colors.ENDC} "
          f"| {cat_type:<15} | {confidence_color}Conf: {confidence:.2f}{Colors.ENDC}")


def display_fashion_results(results: dict, scenario_name: str):
    """Display fashion analysis results in a beautiful format."""

    print_header(f"Fashion Analysis Results - {scenario_name.upper()}")

    # Execution Info
    exec_info = results.get("execution_info", {})
    print_section("Execution Summary")

    success = exec_info.get("success", False)
    success_icon = "✅" if success else "❌"

    print(
        f"   {success_icon} Status: {Colors.GREEN if success else Colors.RED}{Colors.BOLD}{'SUCCESS' if success else 'FAILED'}{Colors.ENDC}")
    print(f"   🔄 Workflow: {exec_info.get('workflow', 'Unknown')}")
    print(f"   🤖 Model Calls: {exec_info.get('model_calls', 'Unknown')}")
    print(f"   ⏱️  Estimated Time: {exec_info.get('estimated_time', 'Unknown')}")

    if not success:
        error = results.get("error", "Unknown error")
        print(f"   {Colors.RED}❌ Error: {error}{Colors.ENDC}")
        return

    # Find the main analysis source
    analysis_sources = ["merged_tags", "conversation_tags", "image_tags", "extracted_tags", "refined_tags"]
    main_source = None
    main_data = None

    for source in analysis_sources:
        if source in results and results[source]:
            main_source = source
            main_data = results[source]
            break

    if not main_data:
        print(f"   {Colors.YELLOW}⚠️  No analysis data found{Colors.ENDC}")
        return

    # Display Main Analysis Results
    print_section(f"Main Analysis Results ({main_source})")

    # Entities
    entities = main_data.get("entities", [])
    if entities:
        print(f"\n   {Colors.BOLD}🏷️  Fashion Entities ({len(entities)} found):{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'#':<3} {'Name':<20} | {'Details':<50} | {'Confidence'}{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'-' * 3} {'-' * 20} | {'-' * 50} | {'-' * 10}{Colors.ENDC}")

        for i, entity in enumerate(entities[:10], 1):  # Show top 10
            print_entity(entity, i)

        if len(entities) > 10:
            print(f"   {Colors.YELLOW}   ... and {len(entities) - 10} more entities{Colors.ENDC}")
    else:
        print(f"   {Colors.YELLOW}⚠️  No entities found{Colors.ENDC}")

    # Categories
    categories = main_data.get("categories", [])
    if categories:
        print(f"\n   {Colors.BOLD}📂 Fashion Categories ({len(categories)} found):{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'#':<3} {'Category':<30} | {'Type':<15} | {'Confidence'}{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'-' * 3} {'-' * 30} | {'-' * 15} | {'-' * 10}{Colors.ENDC}")

        for i, category in enumerate(categories[:5], 1):  # Show top 5
            print_category(category, i)

        if len(categories) > 5:
            print(f"   {Colors.YELLOW}   ... and {len(categories) - 5} more categories{Colors.ENDC}")
    else:
        print(f"   {Colors.YELLOW}⚠️  No categories found{Colors.ENDC}")

    # Attributes Summary
    attributes = main_data.get("attributes", {})
    visual_attributes = main_data.get("visual_attributes", {})
    all_attributes = {**attributes, **visual_attributes}

    if all_attributes:
        print(f"\n   {Colors.BOLD}🎨 Fashion Attributes ({len(all_attributes)} types):{Colors.ENDC}")
        for attr_name, attr_values in list(all_attributes.items())[:5]:  # Show top 5
            if isinstance(attr_values, list):
                values_str = ", ".join(attr_values[:3])
                if len(attr_values) > 3:
                    values_str += f" (+{len(attr_values) - 3} more)"
            else:
                values_str = str(attr_values)

            print(f"   {Colors.BLUE}•{Colors.ENDC} {Colors.BOLD}{attr_name}:{Colors.ENDC} {values_str}")

    # Summary
    if "summary" in main_data and main_data["summary"]:
        print_section("Analysis Summary")
        summary = main_data["summary"]
        # Wrap long summaries
        if len(summary) > 100:
            summary = summary[:100] + "..."
        print(f"   {Colors.ITALIC}{summary}{Colors.ENDC}")

    # Translation Results
    translation_sources = ["persian_output", "target_language_output"]
    for trans_source in translation_sources:
        if trans_source in results and results[trans_source]:
            trans_data = results[trans_source]

            print_section(f"Translation Results ({trans_source})")

            trans_entities = trans_data.get("entities", [])
            if trans_entities:
                print(f"   {Colors.BOLD}🌐 Persian Entities ({len(trans_entities)} translated):{Colors.ENDC}")

                for i, entity in enumerate(trans_entities[:5], 1):  # Show top 5
                    name = entity.get("name", "Unknown")
                    if "values" in entity:
                        values = entity.get("values", [])
                        values_str = ", ".join(values[:2]) if isinstance(values, list) else str(values)
                    else:
                        values_str = entity.get("type", "Unknown")

                    print(f"   {Colors.BLUE}{i:2d}.{Colors.ENDC} {Colors.BOLD}{name}{Colors.ENDC} → {values_str}")

                if len(trans_entities) > 5:
                    print(
                        f"   {Colors.YELLOW}   ... and {len(trans_entities) - 5} more translated entities{Colors.ENDC}")

            break

    # Quality Metrics
    if "quality_score" in main_data:
        quality_score = main_data["quality_score"]
        quality_color = Colors.GREEN if quality_score > 0.8 else Colors.YELLOW if quality_score > 0.6 else Colors.RED
        print(f"\n   {Colors.BOLD}📊 Quality Score: {quality_color}{quality_score:.2f}/1.00{Colors.ENDC}")

    # Error Information
    if "errors" in results and results["errors"]:
        print_section("Execution Errors")
        errors = results["errors"]
        for i, error in enumerate(errors[:3], 1):
            node = error.get("node", "Unknown")
            error_msg = error.get("error", "Unknown error")
            print(f"   {Colors.RED}{i}. {node}: {error_msg[:80]}...{Colors.ENDC}")


def running_scenarios_beautifully():
    """Test scenarios with beautiful output."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print_header("Workflow v2 Fashion Analysis Testing", "🌟")
    print(f"{Colors.CYAN}📷 Image: {example_URL}{Colors.ENDC}")
    print(f"{Colors.CYAN}⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

    # Available scenarios
    scenarios = [
        "scenario_zero",  # Ultra-fast
        "scenario_one",  # Comprehensive
        "scenario_two",  # Simple
        "scenario_three",  # Parallel (uncomment to test)
        "scenario_four"    # Conversation (uncomment to test)
    ]

    runner = create_scenario_runner()
    results_summary = {}

    for scenario_name in scenarios:
        print(f"\n{Colors.YELLOW}🚀 Testing {scenario_name}...{Colors.ENDC}")

        start_time = time.time()

        try:
            results = runner.run_scenario(scenario_name, example_URL)
            execution_time = time.time() - start_time

            # Display results beautifully
            display_fashion_results(results, scenario_name)

            # Store summary
            exec_info = results.get("execution_info", {})
            results_summary[scenario_name] = {
                "success": exec_info.get("success", False),
                "execution_time": execution_time,
                "model_calls": exec_info.get("model_calls", "Unknown")
            }

            print(f"\n{Colors.GREEN}✅ {scenario_name} completed in {execution_time:.1f} seconds{Colors.ENDC}")

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"\n{Colors.RED}❌ {scenario_name} failed after {execution_time:.1f} seconds: {str(e)}{Colors.ENDC}")

            results_summary[scenario_name] = {
                "success": False,
                "execution_time": execution_time,
                "error": str(e)
            }

    # Final Summary
    print_header("Execution Summary")

    print(f"\n{Colors.BOLD}📊 Performance Summary:{Colors.ENDC}")
    print(f"   {Colors.BLUE}{'Scenario':<15} {'Status':<10} {'Time':<10} {'Models':<10}{Colors.ENDC}")
    print(f"   {Colors.BLUE}{'-' * 15} {'-' * 10} {'-' * 10} {'-' * 10}{Colors.ENDC}")

    for scenario_name, summary in results_summary.items():
        status = f"{Colors.GREEN}✅ SUCCESS{Colors.ENDC}" if summary["success"] else f"{Colors.RED}❌ FAILED{Colors.ENDC}"
        time_str = f"{summary['execution_time']:.1f}s"
        models = str(summary.get('model_calls', '?'))

        print(f"   {scenario_name:<15} {status:<20} {time_str:<10} {models:<10}")

    # Speed ranking
    successful = {k: v for k, v in results_summary.items() if v["success"]}
    if successful:
        sorted_by_speed = sorted(successful.items(), key=lambda x: x[1]['execution_time'])

        print(f"\n{Colors.BOLD}🏆 Speed Ranking:{Colors.ENDC}")
        for i, (scenario_name, data) in enumerate(sorted_by_speed, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
            print(f"   {medal} {i}. {scenario_name}: {data['execution_time']:.1f}s")

    print(f"\n{Colors.GREEN}🎉 Testing completed! {Colors.ENDC}")


if __name__ == "__main__":
    running_scenarios_beautifully()
