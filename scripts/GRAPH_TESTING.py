# Simple usage
from src.service.workflow_v2 import create_scenario_runner

example_URL = "https://image.torob.com/base/images/86/EL/86ELVwp4Q_NClfU6.jpg"
runner = create_scenario_runner()
results = runner.run_scenario("scenario_one", example_URL)

# Or even simpler
from src.service.workflow_v2 import run_scenario_from_url

results = run_scenario_from_url("scenario_two", example_URL)

# Advanced usage
from src.service.workflow_v2 import ScenarioOne, get_config

config = get_config()
scenario = ScenarioOne(config.model.__dict__)
results = scenario.execute(example_URL)
