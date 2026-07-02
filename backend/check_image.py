import os
from PIL import Image

media_dir = '/var/www/media/landing'
for name in os.listdir(media_dir):
    path = os.path.join(media_dir, name)
    if os.path.isfile(path) and name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
        try:
            img = Image.open(path)
            print(name, "Dimensions:", img.size)
        except Exception as e:
            print(name, "Error:", e)
