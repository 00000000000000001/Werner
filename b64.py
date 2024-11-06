from pdf2image import convert_from_path
import base64
from io import BytesIO
from PIL import Image

import base64
from PIL import Image
from io import BytesIO

def png_to_base64(png_file: str) -> str:
    print(f"Converting page {png_file} to base64.")

    with Image.open(png_file) as img:
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    return img_b64
