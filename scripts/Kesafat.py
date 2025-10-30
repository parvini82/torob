from pathlib import Path
from src.service.workflow.langgraph_service import run_langgraph_on_url

x = Path("data/processed/toy_sample.json")
# print(x.absolute())

project_root = Path(__file__).resolve().parent
# print(project_root.absolute())

image_url = "https://image.torob.com/base/images/3H/_p/3H_p6gxOjgPpU9vv.jpg"
# output_model = run_langgraph_on_url(image_url)
output_model = {
    "english": {},
    "persian": {
        "entities": [
            {"name": "نوع کلی", "values": ["پیراهن", "شلوار"]},
            {"name": "رنگ", "values": ["مشکی"]},
            {
                "name": "ویژگی های سبک",
                "values": ["یقه بدون درز", "آستین بلند", "گشاد و روان"],
            },
            {"name": "طرح", "values": ["ساده"]},
            {"name": "ویژگی های خاص", "values": ["بند جلویی"]},
            {"name": "اندازه مناسب", "values": ["راحتی"]},
            {"name": "جنس", "values": ["پنبه"]},
            {"name": "برند", "values": ["قابل مشاهده نیست"]},
            {"name": "اندازه", "values": ["قابل مشاهده نیست"]},
        ]
    },
}
# print(output_model.get("persian").get("entities"))


image_url2 = "https://image.torob.com/base/images/Ls/z7/Lsz71VTLh8xUdBLL.jpg"
from src.service.workflow.langgraph_service import run_langgraph_on_url

output_model2 = run_langgraph_on_url(image_url2)
print(output_model2)
