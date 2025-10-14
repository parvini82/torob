from PIL import Image

def predict_tags(image):
    # به صورت نمایشی
    img = Image.open(image.file)
    # اینجا مدل اصلی لود و پیش‌بینی انجام میشه
    return ["car", "road", "sky"]
