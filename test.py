import os

os.environ["FLAGS_use_mkldnn"] = "0"

from paddleocr import PaddleOCR
from PIL import Image
import numpy as np

ocr = PaddleOCR(
    use_textline_orientation=True,
    lang="en",
)

img = np.array(Image.open("sample_table.png").convert("RGB"))

print(ocr.predict(img))