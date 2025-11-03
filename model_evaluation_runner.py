#!/usr/bin/env python3
"""
Model Evaluation Runner - Automated model testing and comparison

This script:
1. Tests lists of Vision and Translation models on OpenRouter
2. Updates the .env file for each model combination
3. Runs prediction and evaluation scripts
4. Compares results across all model combinations
"""

import os
import subprocess
import re
import sys
from pathlib import Path
import itertools

# List of Vision models to test
VISION_MODEL_ALTERNATIVES = [
    # "x-ai/grok-4-fast",
    # "google/gemma-3-12b-it",
    # "openai/gpt-5-mini",
    # "openai/gpt-5",
    # "google/gemma-3-27b-it",
    # "openai/gpt-4o",
    "anthropic/claude-3.5-haiku",
    # "google/gemma-3-4b-it",

]

# List of Translation models to test
TRANSLATE_MODEL_ALTERNATIVES = [
    "openai/gpt-4o-mini",
    "tngtech/deepseek-r1t2-chimera:free",
    "deepseek/deepseek-chat-v3-0324",
    "deepseek/deepseek-chat-v3.1",
]


def update_env_file(vision_model, translate_model):
    """
    Update the .env file with new models

    Args:
        vision_model (str): Name of the vision model
        translate_model (str): Name of the translation model

    Returns:
        bool: True if successful, False otherwise
    """
    env_file_path = Path(".env")

    # If .env doesn't exist, copy from .env.example
    if not env_file_path.exists():
        env_example_path = Path(".env.example")
        if env_example_path.exists():
            with open(env_example_path, 'r', encoding='utf-8') as f:
                content = f.read()
            with open(env_file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Created .env file from .env.example")
        else:
            print("Neither .env nor .env.example files exist!")
            return False

    # Read the .env file content
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading .env file: {e}")
        return False

    # Replace both VISION_MODEL and TRANSLATE_MODEL variables
    updates = [
        (r'^VISION_MODEL=.*$', f'VISION_MODEL={vision_model}'),
        (r'^TRANSLATE_MODEL=.*$', f'TRANSLATE_MODEL={translate_model}')
    ]

    updated_content = content
    for pattern, new_line in updates:
        if re.search(pattern, updated_content, re.MULTILINE):
            # If the variable exists, replace it
            updated_content = re.sub(pattern, new_line, updated_content, flags=re.MULTILINE)
        else:
            # If the variable doesn't exist, add it
            updated_content = updated_content + f'\n{new_line}\n'

    # Write the updated content
    try:
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print(f"✅ VISION_MODEL updated to {vision_model}")
        print(f"✅ TRANSLATE_MODEL updated to {translate_model}")
        return True
    except Exception as e:
        print(f"Error writing .env file: {e}")
        return False


def run_script(script_path):
    """
    Execute a Python script with real-time output streaming

    Args:
        script_path (str): Path to the script

    Returns:
        bool: True if execution is successful, False otherwise
    """
    try:
        print(f"🚀 Running {script_path}...")
        print(f"{'─' * 50}")

        # Run with real-time output streaming
        process = subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            encoding='utf-8',
            bufsize=1,  # Line buffered
            universal_newlines=True
        )

        # Stream output in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Get the final return code
        return_code = process.poll()

        print(f"{'─' * 50}")
        if return_code == 0:
            print(f"✅ {script_path} executed successfully")
            return True
        else:
            print(f"❌ {script_path} failed with return code: {return_code}")
            return False

    except Exception as e:
        print(f"❌ Unexpected error running {script_path}: {e}")
        return False


def validate_scripts():
    """
    Check if all required scripts exist

    Returns:
        bool: True if all scripts exist, False otherwise
    """
    required_scripts = [
        "scripts/run_model_predictions.py",
        "scripts/evaluate_predictions_full.py",
        "scripts/compare_evaluations.py"
    ]

    missing_scripts = []
    for script in required_scripts:
        if not Path(script).exists():
            missing_scripts.append(script)

    if missing_scripts:
        print("❌ Missing required scripts:")
        for script in missing_scripts:
            print(f"   - {script}")
        return False

    return True


def main():
    """
    Main function that executes all the steps
    """
    # Generate all combinations of vision and translation models
    model_combinations = list(itertools.product(VISION_MODEL_ALTERNATIVES, TRANSLATE_MODEL_ALTERNATIVES))

    print("🎯 Starting Model Evaluation")
    print(f"Vision models: {len(VISION_MODEL_ALTERNATIVES)}")
    print(f"Translation models: {len(TRANSLATE_MODEL_ALTERNATIVES)}")
    print(f"Total combinations to test: {len(model_combinations)}")

    # Show the combinations that will be tested
    print("\n📋 Model combinations to test:")
    for i, (vision, translate) in enumerate(model_combinations, 1):
        print(f"  {i:2d}. Vision: {vision}")
        print(f"      Translation: {translate}")

    # Ask for confirmation
    response = input(f"\nProceed with testing {len(model_combinations)} combinations? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled by user")
        return

    # Validate that all required scripts exist
    if not validate_scripts():
        print("❌ Cannot proceed without required scripts")
        return

    # Main loop for each model combination
    successful_combinations = []
    failed_combinations = []

    for i, (vision_model, translate_model) in enumerate(model_combinations, 1):
        print(f"\n{'=' * 80}")
        print(f"📊 Combination {i}/{len(model_combinations)}")
        print(f"Vision: {vision_model}")
        print(f"Translation: {translate_model}")
        print(f"{'=' * 80}")

        # Step 1: Update .env file
        if not update_env_file(vision_model, translate_model):
            print(f"❌ Failed to update .env for combination {i}")
            failed_combinations.append((vision_model, translate_model))
            continue

        # Step 2: Run prediction script
        if not run_script("scripts/run_model_predictions.py"):
            print(f"❌ Failed to run predictions for combination {i}")
            failed_combinations.append((vision_model, translate_model))
            continue

        # Step 3: Run evaluation script
        if not run_script("scripts/evaluate_predictions_full.py"):
            print(f"❌ Failed to run evaluation for combination {i}")
            failed_combinations.append((vision_model, translate_model))
            continue

        successful_combinations.append((vision_model, translate_model))
        print(f"✅ Combination {i} processed successfully")

    # Final step: Compare evaluations
    print(f"\n{'=' * 80}")
    print("🔍 Running final comparison...")
    print(f"{'=' * 80}")

    if successful_combinations:
        if run_script("scripts/compare_evaluations.py"):
            print("✅ Final comparison completed successfully")
        else:
            print("❌ Error running final comparison")
    else:
        print("❌ No combinations processed successfully, cannot run comparison")

    # Final report
    print(f"\n{'=' * 80}")
    print("📈 Final Report")
    print(f"{'=' * 80}")
    print(f"✅ Successful combinations ({len(successful_combinations)}):")
    for i, (vision, translate) in enumerate(successful_combinations, 1):
        print(f"  {i:2d}. Vision: {vision}")
        print(f"      Translation: {translate}")

    if failed_combinations:
        print(f"\n❌ Failed combinations ({len(failed_combinations)}):")
        for i, (vision, translate) in enumerate(failed_combinations, 1):
            print(f"  {i:2d}. Vision: {vision}")
            print(f"      Translation: {translate}")

    print(f"\n🎯 Total: {len(model_combinations)} combinations, "
          f"Successful: {len(successful_combinations)}, "
          f"Failed: {len(failed_combinations)}")


if __name__ == "__main__":
    main()
