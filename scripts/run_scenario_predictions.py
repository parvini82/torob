#!/usr/bin/env python3
# File: scripts/run_scenario_predictions.py
# Purpose: Run workflow_v2 scenarios on a toy sample and save predictions for evaluation.

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Ensure project root in PYTHONPATH
script_dir = Path(__file__).parent
project_root = script_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from evaluation import ModelRunner, EvaluationConfig  # uses evaluation/model_runner.py
from scripts.run_model_predictions import find_toy_sample, save_prediction_results
from src.service.workflow_v2 import run_scenario_from_url  # convenience API


def create_scenario_model_function(scenario_name: str):
    """Returns a callable(image_url) -> List[Dict[str, Any]] that runs the given scenario."""
    def scenario_model_function(image_url: str) -> List[Dict[str, Any]]:
        MAX_RETRIES = 3
        BASE_DELAY = 5
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    delay = BASE_DELAY * (2 ** (attempt - 1))
                    print(f"    Retry {attempt + 1} for {image_url[:50]}... (waiting {delay}s)")
                    time.sleep(delay)

                print(f"    Running {scenario_name} on {image_url[:50]}...")
                output_model = run_scenario_from_url(scenario_name, image_url)

                if not output_model:
                    raise ValueError("Scenario returned empty result")

                persian = output_model.get("persian", {})
                entities = persian.get("entities")
                if not isinstance(entities, list):
                    raise KeyError("persian.entities is missing or not a list")

                return entities

            except Exception as e:
                print(f"    ⚠ Error on attempt {attempt + 1}: {e}")
                if attempt == MAX_RETRIES - 1:
                    print(f"    ✗ Failed after {MAX_RETRIES} attempts: {image_url[:60]}...")
                    return []
        return []
    return scenario_model_function


def get_current_scenario() -> str:
    """Get scenario name from env or config file; default 'scenario_one'."""
    scenario = os.getenv("CURRENT_SCENARIO", "scenario_one")
    cfg = project_root / "current_scenario.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            scenario = data.get("scenario", scenario)
        except Exception:
            pass
    return scenario


def main():
    print("=" * 80)
    print("SCENARIO PREDICTION RUNNER")
    print("=" * 80)

    current_scenario = get_current_scenario()
    print(f"Scenario: {current_scenario}")

    models_config = {
        "vision": os.getenv("VISION_MODEL", "openai/gpt-4o"),
        "translation": os.getenv("TRANSLATE_MODEL", "openai/gpt-4o-mini"),
        "refiner": os.getenv("REFINER_MODEL", "openai/gpt-4o"),
    }
    print("Models:")
    for k, v in models_config.items():
        print(f"  {k}: {v}")

    sample_path = find_toy_sample()
    if not sample_path:
        print("❌ No toy sample found under data/processed. Generate one first.")
        return False
    print(f"Sample: {sample_path.name}")

    # Place results under evaluation/scenario_predictions
    config = EvaluationConfig(
        results_dir=project_root / "evaluation" / "scenario_predictions",
        model_name=f"{current_scenario}_{models_config['vision'].replace('/', '_')}"
    )

    runner = ModelRunner(config)
    scenario_fn = create_scenario_model_function(current_scenario)

    try:
        results = runner.run_model_on_sample(
            sample_path=sample_path,
            model_function=scenario_fn
        )

        # Save with clear scenario-based naming
        output_filename = f"predictions_{config.model_name}_{sample_path.stem}.json"
        output_path = config.results_dir / output_filename

        # Attach scenario metadata
        results["scenario_metadata"] = {
            "scenario": current_scenario,
            "models": models_config
        }

        save_prediction_results(results, output_path)

        print(f"\n🎉 Done. Saved: {output_path}")
        print(f"Next: python scripts/evaluate_scenarios_full.py")
        return True
    except Exception as e:
        print(f"\n❌ Scenario prediction failed: {e}")
        return False


if __name__ == "__main__":
    ok = main()
    if not ok:
        sys.exit(1)
