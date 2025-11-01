# Simple usage
from src.service.workflow_v2 import create_scenario_runner
import logging
import time

# Disable all logging output
logging.disable(logging.CRITICAL)


scenarios_name = [
    "scenario_one", "scenario_two", "scenario_three", "scenario_four",
                  "scenario_zero"]
for scenario_name in scenarios_name:
    print(scenario_name)
    example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"
    runner = create_scenario_runner()
    results = runner.run_scenario(scenario_name, example_URL)
    print(results.items())

    if "persian_output" in results:
        print("farsi : ", results["persian_output"])
    else:
        print("farsi : nadasht")

    # for source in ["merged_tags", "conversation_tags", "extracted_tags", "image_tags",
    #                "persian_output", "target_language_output"]:
    #     if source in results:
    #         print(f"{source}: {results[source]}")
        # entities = len(results[source].get("entities", []))
        # categories = len(results[source].get("categories", []))
        # print(f"   📊 {source}: {entities} entities, {categories} categories")
        # print(f"{source}: {len(results[source].get('entities', []))} entities")
        # print(f"{source}: {len(results[source].get('categories', []))} categories")
        # break
        # if "persian_output" in results:
        #     print("farsi : ",results["persian_output"])
        # else:
        #     print("farsi : nadasht")

# # Or even simpler
# from src.service.workflow_v2 import run_scenario_from_url
#
# results = run_scenario_from_url("scenario_two", example_URL)
#
# # Advanced usage
# from src.service.workflow_v2 import ScenarioOne, get_config
#
# config = get_config()
# scenario = ScenarioOne(config.model.__dict__)
# results = scenario.execute(example_URL)
