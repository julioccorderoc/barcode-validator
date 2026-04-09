import cv2
import numpy as np
from PIL import Image


def preprocess(image: Image.Image) -> Image.Image:
    """Apply preprocessing to improve barcode detection.

    Pipeline (ADR-003): Grayscale → Gaussian blur (5x5) → Otsu threshold.
    Returns a binary PIL Image suitable for barcode decoding retry.
    """
    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)
