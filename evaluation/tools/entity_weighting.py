# File: evaluation/tools/build_entity_weights.py

import json
from pathlib import Path
from collections import defaultdict, Counter


def build_entity_weights(data_folder_path: str, output_path: str):
    """
    Build entity weights from JSON files in a folder.

    Args:
        data_folder_path: Path to folder containing JSON files
        output_path: Where to save the weights JSON
    """
    data_folder = Path(data_folder_path)
    print(data_folder)

    # Step 1: Count entity frequencies per category
    category_entity_freq = defaultdict(Counter)

    # Read all JSON files in folder
    for json_file in data_folder.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle both list of records and single record
        if isinstance(data, list):
            records = data
        else:
            records = [data]

        for record in records:
            category = record.get("product", "unknown")
            entities = record.get("entities", [])

            for entity in entities:
                entity_name = entity.get("name", "").strip().lower()
                if entity_name:
                    category_entity_freq[category][entity_name] += 1

    # Step 2: Normalize weights within each category
    category_weights = {}
    for category, entity_counts in category_entity_freq.items():
        total = sum(entity_counts.values())
        if total > 0:
            category_weights[category] = {
                entity_name: count / total
                for entity_name, count in entity_counts.items()
            }

    # Step 3: Save to JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(category_weights, f, ensure_ascii=False, indent=2)

    print(f"Entity weights saved to: {output_path}")
    return category_weights


if __name__ == "__main__":
    # Usage example:
    data_folder = "data/raw/extracted/entities_dataset_v2"
    output_file = "evaluation/results/entity_weights.json"

    weights = build_entity_weights(data_folder, output_file)
