#!/usr/bin/env python3
# File: scenario_evaluation_runner.py

import os
import re
import sys
import itertools
import subprocess
from pathlib import Path

project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

SCENARIOS = ["scenario_zero", "scenario_one", "scenario_two", "scenario_three", "scenario_four"]

VISION_MODELS = [
    "openai/gpt-4o",
    # "anthropic/claude-3.5-haiku",
]

TRANSLATION_MODELS = [
    "openai/gpt-4o-mini",
    # "deepseek/deepseek-chat-v3.1",
]

REFINER_MODELS = [
    "openai/gpt-4o",
]

def update_env(models):
    env_file = project_root / ".env"
    content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
    updates = [
        (r"^VISION_MODEL=.*$", f"VISION_MODEL={models['vision']}"),
        (r"^TRANSLATE_MODEL=.*$", f"TRANSLATE_MODEL={models['translation']}"),
        (r"^REFINER_MODEL=.*$", f"REFINER_MODEL={models.get('refiner','')}"),
    ]
    for pattern, new_line in updates:
        if re.search(pattern, content, re.MULTILINE):
            content = re.sub(pattern, new_line, content, flags=re.MULTILINE)
        else:
            content += f"\n{new_line}\n"
    env_file.write_text(content, encoding="utf-8")

def run(cmd, env=None):
    print("─" * 80)
    print("RUN:", " ".join(cmd))
    print("─" * 80)
    proc = subprocess.Popen(
        cmd,
        cwd=project_root,
        env=env or os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=0,
    )
    for line in proc.stdout:
        print(line.rstrip())
        sys.stdout.flush()
    return proc.wait() == 0

def main():
    combinations = []
    for scenario in SCENARIOS:
        for vision, trans in itertools.product(VISION_MODELS, TRANSLATION_MODELS):
            for refiner in REFINER_MODELS:
                combinations.append({
                    "scenario": scenario,
                    "models": {"vision": vision, "translation": trans, "refiner": refiner}
                })

    ok_count = 0
    for i, combo in enumerate(combinations, 1):
        print(f"\n=== [{i}/{len(combinations)}] Scenario {combo['scenario']} ===")
        os.environ["CURRENT_SCENARIO"] = combo["scenario"]
        update_env(combo["models"])

        # Ensure PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        if not run([sys.executable, "scripts/run_scenario_predictions.py"], env=env):
            print("Prediction failed; continuing to next combo.")
            continue
        if not run([sys.executable, "scripts/evaluate_scenarios_full.py"], env=env):
            print("Evaluation failed; continuing to next combo.")
            continue

        ok_count += 1

    print(f"\nFinished. Successful combos: {ok_count}/{len(combinations)}")

if __name__ == "__main__":
    main()
