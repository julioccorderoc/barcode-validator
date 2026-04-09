import numpy as np
from PIL import Image

from barcode_validator.preprocessing import preprocess


def test_preprocess_returns_pil_image():
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    result = preprocess(img)
    assert isinstance(result, Image.Image)


def test_preprocess_output_is_grayscale_binary():
    """Otsu threshold should produce a binary (black/white) image."""
    arr = np.zeros((100, 200, 3), dtype=np.uint8)
    arr[:, :100] = 255  # left half white
    arr[:, 100:] = 0    # right half black
    img = Image.fromarray(arr, "RGB")
    result = preprocess(img)
    result_arr = np.array(result)
    unique_values = set(np.unique(result_arr))
    assert unique_values <= {0, 255}


def test_preprocess_preserves_dimensions():
    img = Image.new("RGB", (300, 150))
    result = preprocess(img)
    assert result.size == (300, 150)
