import os
os.environ["PADDLE_PDX_ENABLE_MKLDNN_BYDEFAULT"] = "0"

from paddleocr import PaddleOCR

ocr = PaddleOCR()

results = ocr.predict("sample_table.png")

results[0].save_to_json("ocr_output.json")

print("Saved!")