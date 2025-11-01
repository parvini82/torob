"""
Clean Persian Tags Display - No Logs, Just Results.
Shows only Persian translation results in a beautiful format.
"""
from scripts_2.Zero import running_scenario_zero
from src.service.workflow_v2 import create_scenario_runner
import logging
import time

# Disable all logging output
logging.disable(logging.CRITICAL)


class Colors:
    """ANSI color codes for formatted terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(title: str):
    """Print a formatted header in terminal."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}")
    print("═" * 80)
    print(f"{title:^80}")
    print("═" * 80)
    print(f"{Colors.ENDC}")


def display_persian_tags(results: dict, scenario_name: str):
    """Display only Persian translation results from the scenario output."""

    print(f"\n{Colors.CYAN}{Colors.BOLD}🌐 {scenario_name.upper()} - نتایج فارسی{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─' * 50}{Colors.ENDC}")

    # Locate Persian output data (in either key)
    persian_data = None
    for source in ["persian_output", "target_language_output"]:
        if source in results and results[source]:
            persian_data = results[source]
            break

    if not persian_data:
        print(f"   {Colors.RED}❌ هیچ ترجمه فارسی پیدا نشد{Colors.ENDC}")
        return

    # Display Persian entities
    entities = persian_data.get("entities", [])
    if entities:
        print(f"\n   {Colors.BOLD}🏷️  تگ های فارسی ({len(entities)} عدد):{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'ردیف':<5} {'نام':<25} {'مقادیر':<40}{Colors.ENDC}")
        print(f"   {Colors.BLUE}{'-' * 5} {'-' * 25} {'-' * 40}{Colors.ENDC}")

        for i, entity in enumerate(entities, 1):
            name = entity.get("name", "نامشخص")

            # Handle both possible structures: with or without "values" key
            if "values" in entity:
                values = entity.get("values", [])
                if isinstance(values, list):
                    values_str = "، ".join(values[:3])  # Persian comma
                    if len(values) > 3:
                        values_str += f" (و {len(values) - 3} مورد دیگر)"
                else:
                    values_str = str(values)
            else:
                values_str = entity.get("type", "نامشخص")

            # Truncate long value strings for readability
            if len(values_str) > 35:
                values_str = values_str[:35] + "..."

            print(f"   {Colors.BLUE}{i:<5}{Colors.ENDC} {Colors.BOLD}{name:<25}{Colors.ENDC} {values_str}")
    else:
        print(f"   {Colors.YELLOW}⚠️  هیچ تگی پیدا نشد{Colors.ENDC}")

    # Display Persian categories
    categories = persian_data.get("categories", [])
    if categories:
        print(f"\n   {Colors.BOLD}📂 دسته‌بندی‌های فارسی ({len(categories)} عدد):{Colors.ENDC}")
        for i, category in enumerate(categories, 1):
            name = category.get("name", "نامشخص")
            cat_type = category.get("type", category.get("level", "عمومی"))
            print(f"   {Colors.BLUE}{i}.{Colors.ENDC} {Colors.BOLD}{name}{Colors.ENDC} ({cat_type})")

    # Display Persian attributes (merged from both normal and visual)
    attributes = persian_data.get("attributes", {})
    visual_attributes = persian_data.get("visual_attributes", {})
    all_attributes = {**attributes, **visual_attributes}

    if all_attributes:
        print(f"\n   {Colors.BOLD}🎨 ویژگی‌های فارسی ({len(all_attributes)} نوع):{Colors.ENDC}")
        for attr_name, attr_values in all_attributes.items():
            if isinstance(attr_values, list):
                values_str = "، ".join(attr_values[:3])
                if len(attr_values) > 3:
                    values_str += f" (و {len(attr_values) - 3} مورد دیگر)"
            else:
                values_str = str(attr_values)

            print(f"   {Colors.BLUE}•{Colors.ENDC} {Colors.BOLD}{attr_name}:{Colors.ENDC} {values_str}")

    # Display Persian summary (if available)
    if "summary" in persian_data and persian_data["summary"]:
        summary = persian_data["summary"]
        if len(summary) > 100:
            summary = summary[:100] + "..."
        print(f"\n   {Colors.BOLD}📝 خلاصه:{Colors.ENDC} {summary}")


def running_persian_tags():
    """Test multiple scenarios and show only Persian results."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print_header("🇮🇷 تست تگ‌های فارسی - بدون لاگ")
    print(f"{Colors.CYAN}📷 تصویر: {example_URL.split('/')[-1]}{Colors.ENDC}")

    # Define test scenarios
    scenarios = [
        "scenario_zero",  # Fastest
        "scenario_one",  # Full version
        "scenario_two",  # Simplified
        # "scenario_three",  # Parallel (uncomment to test)
        # "scenario_four"    # Conversational (uncomment to test)
    ]

    runner = create_scenario_runner()

    for scenario_name in scenarios:
        print(f"\n{Colors.YELLOW}🚀 در حال تست {scenario_name}...{Colors.ENDC}")

        start_time = time.time()

        try:
            results = runner.run_scenario(scenario_name, example_URL)
            execution_time = time.time() - start_time

            # Show only Persian translation part
            display_persian_tags(results, scenario_name)

            print(f"\n{Colors.GREEN}✅ {scenario_name} تکمیل شد در {execution_time:.1f} ثانیه{Colors.ENDC}")

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"\n{Colors.RED}❌ {scenario_name} ناموفق بود پس از {execution_time:.1f} ثانیه{Colors.ENDC}")
            print(f"   خطا: {str(e)}")

    print(f"\n{Colors.GREEN}🎉 تست کامل شد!{Colors.ENDC}")


def running_single_scenario_persian(scenario_name: str = "scenario_zero"):
    """Test a single scenario and show detailed Persian results."""

    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"

    print_header(f"🔍 تست تفصیلی {scenario_name} - فقط فارسی")

    runner = create_scenario_runner()

    print(f"{Colors.YELLOW}🚀 در حال اجرای {scenario_name}...{Colors.ENDC}")

    start_time = time.time()

    try:
        results = runner.run_scenario(scenario_name, example_URL)
        execution_time = time.time() - start_time

        # Show detailed Persian results
        display_persian_tags(results, scenario_name)

        # Display execution metadata
        exec_info = results.get("execution_info", {})
        print(f"\n{Colors.BLUE}📊 اطلاعات اجرا:{Colors.ENDC}")
        print(f"   ⏱️  زمان: {execution_time:.1f} ثانیه")
        print(f"   🤖 تعداد فراخوانی مدل: {exec_info.get('model_calls', 'نامشخص')}")
        print(f"   ✅ وضعیت: {'موفق' if exec_info.get('success') else 'ناموفق'}")

        print(f"\n{Colors.GREEN}🎉 تست با موفقیت انجام شد!{Colors.ENDC}")

    except Exception as e:
        execution_time = time.time() - start_time
        print(f"\n{Colors.RED}❌ تست ناموفق بود پس از {execution_time:.1f} ثانیه{Colors.ENDC}")
        print(f"   خطا: {str(e)}")


if __name__ == "__main__":
    # Run all scenarios (uncomment the one you prefer)

    running_persian_tags()  # Run all scenarios

    # Or run a single detailed scenario:
    # test_single_scenario_persian("scenario_zero")
