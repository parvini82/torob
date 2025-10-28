# import json
#
# # Define input and output file paths
# input_file = "Ground_Truth.json"
# output_file = "Ground_Truth.json"
#
# # Load the JSON file
# with open(input_file, "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# # Process and transform each record
# new_data = []
# for item in data:
#     # Keep only specific keys and rename "predictions" -> "entities"
#     new_item = {
#         "index": item.get("index"),
#         "image_url": item.get("image_url"),
#         "entities": item.get("predictions", [])
#     }
#     new_data.append(new_item)
#
# # Save the transformed data into a new JSON file
# with open(output_file, "w", encoding="utf-8") as f:
#     json.dump(new_data, f, ensure_ascii=False, indent=2)
#
# print(f"✅ New file saved as: {output_file}")







# import json
#
# # Define the input file path
# input_file = "Ground_Truth.json"
#
# # Load the JSON file
# with open(input_file, "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# # Filter out items where status is not "success"
# failed_items = [item for item in data if item.get("status") != "success"]
#
# # Print the failed items
# print(f"⚠️ Found {len(failed_items)} items with status != 'success':\n")
# for item in failed_items:
#     print(json.dumps(item, ensure_ascii=False, indent=2))
#     print("-" * 80)
# print(data[210])






import json
#
# # Define input and output file paths
# input_file = "Ground_Truth.json"
# output_file = "Ground_Truth_first10.json"
#
# # Load the original JSON file
# with open(input_file, "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# # Take the first 10 items
# first_10 = data[:10]
#
# # Save them into a new file
# with open(output_file, "w", encoding="utf-8") as f:
#     json.dump(first_10, f, ensure_ascii=False, indent=2)
#
# print(f"✅ First 10 items saved to: {output_file}")
#






#
#
#
#
# import json
# from src.service.langgraph.langgraph_service import run_langgraph_on_url
#
# # Define input and output file paths
# input_file = "Ground_Truth.json"
# output_file = "Ground_Truth.json"
#
# # Load the JSON file
# with open(input_file, "r", encoding="utf-8") as f:
#     data = json.load(f)
#
# # Iterate through each record
# for item in data:
#     # Only process items that are not successful
#     if item.get("status") != "success":
#         image_url = item.get("image_url")
#         try:
#             # Run the LangGraph model on the image URL
#             output_model = run_langgraph_on_url(image_url)
#
#             # Safely extract the Persian entities
#             entities = (
#                 output_model.get("persian", {}).get("entities", [])
#                 if isinstance(output_model, dict)
#                 else []
#             )
#
#             # Update the "predictions" field
#             item["predictions"] = entities
#             item["status"] = "success"  # Optionally mark as success now
#
#             print(f"✅ Updated item {item.get('index')} successfully.")
#         except Exception as e:
#             print(f"❌ Error processing item {item.get('index')}: {e}")
#
# # Save the updated data into a new JSON file
# with open(output_file, "w", encoding="utf-8") as f:
#     json.dump(data, f, ensure_ascii=False, indent=2)
#
# print(f"\n💾 Updated data saved to: {output_file}")




import json

# Define the input file path
input_file = "Ground_Truth.json"

# Load the JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Find items where "entities" is empty
empty_entities = [item["index"] for item in data if not item.get("entities")]

# Print results
print(f"⚠️ Found {len(empty_entities)} items with empty 'entities':")
print(empty_entities)







import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from evaluation import ModelRunner, EvaluationConfig

import time
import random
from typing import List, Dict, Any

from src.service.langgraph.langgraph_service import run_langgraph_on_url


def example_model_function(image_url: str) -> List[Dict[str, Any]]:
    """Model function with robust retry logic and error handling.

    Args:
        image_url: URL of product image

    Returns:
        List of entity dictionaries with 'name' and 'values' keys
    """

    # Retry configuration
    MAX_RETRIES = 3
    BASE_DELAY = 20  # Base delay in seconds
    MAX_DELAY = 120  # Maximum delay in seconds

    last_error = None
    total_wait_time = 0

    for attempt in range(MAX_RETRIES + 1):  # +1 for initial attempt
        try:
            if attempt > 0:
                # Calculate delay with exponential backoff + jitter
                delay = min(BASE_DELAY * (2 ** (attempt - 1)), MAX_DELAY)
                # Add random jitter (±20% of delay)
                jitter = random.uniform(-0.2 * delay, 0.2 * delay)
                actual_delay = max(5, delay + jitter)  # Minimum 5 seconds

                print(
                    f"    Attempt {attempt + 1}/{MAX_RETRIES + 1} for {image_url[:50]}... (waiting {actual_delay:.1f}s)")
                time.sleep(actual_delay)
                total_wait_time += actual_delay
            else:
                # Initial sleep to prevent rate limiting
                print(f"    Processing {image_url[:50]}... (initial 20s delay)")
                time.sleep(BASE_DELAY)
                total_wait_time += BASE_DELAY

            # Call the actual model
            output_model = run_langgraph_on_url(image_url)

            # Validate output structure
            if not output_model:
                raise ValueError("Model returned empty/null result")

            if 'persian' not in output_model:
                raise KeyError("'persian' key not found in model output")

            persian_section = output_model.get("persian")
            if not persian_section or 'entities' not in persian_section:
                raise KeyError("'entities' key not found in persian section")

            entities = persian_section.get("entities")
            if not isinstance(entities, list):
                raise TypeError(f"entities is not a list, got: {type(entities)}")

            # Success! Return the entities
            if attempt > 0:
                print(f"    ✓ Success on attempt {attempt + 1} after {total_wait_time:.1f}s total wait time")

            return entities

        except Exception as e:
            last_error = e
            error_type = type(e).__name__
            error_msg = str(e)

            # Check for specific error types that warrant retry
            should_retry = False
            wait_multiplier = 1

            # Rate limiting errors
            if any(keyword in error_msg.lower() for keyword in [
                'rate limit', 'too many requests', '429', 'quota exceeded',
                'rate exceeded', 'throttled'
            ]):
                should_retry = True
                wait_multiplier = 2  # Wait longer for rate limits
                print(f"    ⚠ Rate limit error on attempt {attempt + 1}: {error_msg}")

            # Network/connection errors
            elif any(keyword in error_msg.lower() for keyword in [
                'connection', 'timeout', 'network', 'dns', 'unreachable',
                'connection refused', 'connection reset', 'socket'
            ]):
                should_retry = True
                print(f"    ⚠ Network error on attempt {attempt + 1}: {error_msg}")

            # Server errors (5xx)
            elif any(keyword in error_msg.lower() for keyword in [
                'server error', '500', '502', '503', '504', 'bad gateway',
                'service unavailable', 'gateway timeout', 'internal server error'
            ]):
                should_retry = True
                print(f"    ⚠ Server error on attempt {attempt + 1}: {error_msg}")

            # Temporary service issues
            elif any(keyword in error_msg.lower() for keyword in [
                'temporarily unavailable', 'service busy', 'overloaded',
                'maintenance', 'try again later'
            ]):
                should_retry = True
                wait_multiplier = 1.5
                print(f"    ⚠ Service temporarily unavailable on attempt {attempt + 1}: {error_msg}")

            # Data structure issues (might be temporary)
            elif error_type in ['KeyError', 'TypeError', 'ValueError']:
                should_retry = True
                print(f"    ⚠ Data structure error on attempt {attempt + 1}: {error_msg}")

            else:
                # Unknown error - still try once more, but don't wait as long
                should_retry = True
                wait_multiplier = 0.5
                print(f"    ⚠ Unknown error ({error_type}) on attempt {attempt + 1}: {error_msg}")

            # Check if we should retry
            if attempt < MAX_RETRIES and should_retry:
                # Adjust wait time based on error type
                BASE_DELAY = int(BASE_DELAY * wait_multiplier)
                continue
            else:
                # Final attempt failed or error not worth retrying
                break

    # All retries exhausted
    error_type = type(last_error).__name__ if last_error else "Unknown"
    error_msg = str(last_error) if last_error else "Unknown error"

    print(f"    ✗ Failed after {MAX_RETRIES + 1} attempts and {total_wait_time:.1f}s total wait time")
    print(f"      Final error ({error_type}): {error_msg}")
    print(f"      Returning empty list for: {image_url[:60]}...")

    return []
#
#


import json

# Define input and output file paths
input_file = "Ground_Truth.json"
output_file = "Ground_Truth.json"

# Load the JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Iterate through each record
for item in data:
    # Only process items where "entities" is empty
    if not item.get("entities"):
        image_url = item.get("image_url")
        try:
            # Run the LangGraph model on the image URL
            output_model = example_model_function(image_url)
            entities = output_model if isinstance(output_model, list) else []
            # Safely extract the Persian entities
                # entities = (
                #     output_model.get("persian", {}).get("entities", [])
                #     if isinstance(output_model, dict)
                #     else []
                # )

            # Update the "entities" field
            item["entities"] = entities

            print(f"✅ Filled empty entities for item {item.get('index')}.")
        except Exception as e:
            print(f"❌ Error processing item {item.get('index')}: {e}")

# Save the updated data into the same file (or a new one if you prefer)
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n💾 Updated data saved to: {output_file}")



import json

# Define the input file path
input_file = "Ground_Truth.json"

# Load the JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Find items where "entities" is empty
empty_entities = [item["index"] for item in data if not item.get("entities")]

# Print results
print(f"⚠️ Found {len(empty_entities)} items with empty 'entities':")
print(empty_entities)







