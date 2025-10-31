#!/usr/bin/env python3
"""
Simple test script for all 4 scenarios with dotenv support.
"""

import os
import sys
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    # Check API key
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found!")
        print("Create a .env file with:")
        print("OPENROUTER_API_KEY=your_key_here")
        return

    print(f"✅ API Key loaded: {api_key[:10]}...{api_key[-5:]}")

    # Import and setup
    try:
        from src.service.langgraph_v2.main import ScenarioRunner
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("Make sure you're in the project root directory")
        return

    image_url = "https://image.torob.com/base/images/ST/V0/STV0N9liwgLNmi27.jpg"
    runner = ScenarioRunner()

    # Get available scenarios
    available_scenarios = list(runner.scenarios.keys())
    print(f"📋 Available scenarios: {available_scenarios}")

    print("\n🧪 Testing All Available Scenarios")
    print("=" * 45)
    print(f"📷 Image: {image_url}")
    print()

    results = {}

    for i, scenario in enumerate(available_scenarios, 1):
        print(f"{i}️⃣ Testing {scenario.upper()}")
        print("-" * 30)

        try:
            result = runner.run_scenario(scenario, image_url)

            # Get results
            english = result.get("english_output", {}).get("entities", [])
            persian = result.get("persian_output", {}).get("entities", [])

            results[scenario] = {
                "success": True,
                "english_count": len(english),
                "persian_count": len(persian),
                "english_sample": english[:] if english else [],
                "persian_sample": persian[:] if persian else []
            }

            print(f"✅ SUCCESS")
            print(f"   📊 English: {len(english)} entities")
            print(f"   🇮🇷 Persian: {len(persian)} entities")

            # Show samples
            if english:
                print(f"   🎯 English sample:")
                for entity in english[:]:
                    name = entity.get('name', 'unknown')
                    values = ', '.join(entity.get('values', [])[:3])
                    print(f"      • {name}: {values}")

            if persian:
                print(f"   🎯 Persian sample:")
                for entity in persian[:]:
                    name = entity.get('name', 'unknown')
                    values = ', '.join(entity.get('values', [])[:3])
                    print(f"      • {name}: {values}")

        except Exception as e:
            results[scenario] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ FAILED: {str(e)}")

        print()

    # Summary
    successful = len([r for r in results.values() if r.get("success", False)])
    total = len(results)

    print("📊 SUMMARY")
    print("=" * 15)
    print(f"✅ Successful: {successful}/{total}")
    print(f"📈 Success Rate: {(successful / total) * 100:.1f}%")

    if successful == total:
        print("🎉 All scenarios working perfectly!")
    elif successful > 0:
        print("⚠️  Some scenarios have issues")
    else:
        print("❌ All scenarios failed - check configuration")


if __name__ == "__main__":
    main()
