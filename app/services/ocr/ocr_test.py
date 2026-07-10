import cv2
from paddleocr import PaddleOCR

img = cv2.imread("test.png")

ocr = PaddleOCR(
    text_detection_model_name="PP-OCRv5_mobile_det",
    text_recognition_model_name="PP-OCRv5_mobile_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)

print("OCR Loaded")

result = ocr.predict(img)

print(result)