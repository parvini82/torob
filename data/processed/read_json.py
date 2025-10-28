import json

from torch._dynamo.polyfills import sys


def get_json_object(file_path: str, index: int):
    """Read a JSON file (list of objects) and return the i-th object."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)  # Read and parse JSON file

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list at the top level.")

    if index < 0 or index >= len(data):
        raise IndexError(f"Index {index} is out of range. File contains {len(data)} objects.")

    return data[index]

if __name__ == '__main__':
    with open("toy_sample_high_entity.json", "r", encoding="utf-8") as f:
        data = json.load(f)  # Read and parse JSON file
    for index in range(10):
        print(index,":",data[index])
