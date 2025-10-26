from pathlib import Path

x = Path("data/processed/toy_sample.json")
print(x.absolute())

project_root = Path(__file__).resolve().parent.parent
print(project_root.absolute())
from src.service.langgraph.langgraph_service import run_langgraph_on_url

image_url = "https://image.torob.com/base/images/3H/_p/3H_p6gxOjgPpU9vv.jpg"
output_model = run_langgraph_on_url(image_url)
print(output_model)
