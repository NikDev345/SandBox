"""
Image Processing Utilities
--------------------------
Handles image validation, preprocessing, and enhancement before OCR.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image

# --------------------------------------------------
# Supported Extensions
# --------------------------------------------------

SUPPORTED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".bmp",
    ".tiff",
    ".tif",
    ".webp"
}

MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB


# --------------------------------------------------
# Validation
# --------------------------------------------------

def validate_extension(filename: str) -> bool:
    return Path(filename).suffix.lower() in SUPPORTED_EXTENSIONS


def validate_size(file_size: int) -> bool:
    return file_size <= MAX_FILE_SIZE


# --------------------------------------------------
# Image Loading
# --------------------------------------------------

def load_image(file_bytes: bytes) -> np.ndarray:
    """
    Convert uploaded bytes to OpenCV image.
    """

    image = Image.open(io.BytesIO(file_bytes))

    image = image.convert("RGB")

    return cv2.cvtColor(
        np.array(image),
        cv2.COLOR_RGB2BGR
    )


# --------------------------------------------------
# Basic Operations
# --------------------------------------------------

def resize_image(
    image: np.ndarray,
    max_width: int = 1800
) -> np.ndarray:

    h, w = image.shape[:2]

    if w <= max_width:
        return image

    ratio = max_width / w

    return cv2.resize(
        image,
        (
            int(w * ratio),
            int(h * ratio)
        ),
        interpolation=cv2.INTER_AREA
    )


def grayscale(image: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )


def denoise(image: np.ndarray) -> np.ndarray:
    return cv2.fastNlMeansDenoisingColored(
        image,
        None,
        10,
        10,
        7,
        21
    )


def sharpen(image: np.ndarray) -> np.ndarray:

    kernel = np.array([
        [0, -1, 0],
        [-1, 5, -1],
        [0, -1, 0]
    ])

    return cv2.filter2D(image, -1, kernel)


def increase_contrast(image: np.ndarray) -> np.ndarray:

    lab = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2LAB
    )

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)

    merged = cv2.merge((l, a, b))

    return cv2.cvtColor(
        merged,
        cv2.COLOR_LAB2BGR
    )


def threshold(image: np.ndarray) -> np.ndarray:

    gray = grayscale(image)

    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        11
    )


# --------------------------------------------------
# Rotation
# --------------------------------------------------

def rotate(
    image: np.ndarray,
    angle: float
) -> np.ndarray:

    h, w = image.shape[:2]

    center = (w // 2, h // 2)

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    return cv2.warpAffine(
        image,
        matrix,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE
    )


# --------------------------------------------------
# OCR Preprocessing Pipeline
# --------------------------------------------------

def preprocess_for_ocr(image: np.ndarray) -> np.ndarray:

    image = resize_image(image)

    image = denoise(image)

    image = increase_contrast(image)

    image = sharpen(image)

    image = threshold(image)

    image = cv2.cvtColor(
        image,
        cv2.COLOR_GRAY2BGR
    )

    return image


# --------------------------------------------------
# Statistics
# --------------------------------------------------

def image_dimensions(image: np.ndarray) -> Tuple[int, int]:
    h, w = image.shape[:2]
    return w, h