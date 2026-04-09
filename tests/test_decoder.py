from unittest.mock import patch

from PIL import Image

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import PageImage
from barcode_validator.models import DecodedBarcode


def test_decode_returns_list():
    img = Image.new("RGB", (100, 100), color="white")
    page = PageImage(image=img, page=1)
    result = decode_barcodes([page])
    assert isinstance(result, list)


def test_decode_blank_image_returns_empty():
    """A blank white image has no barcodes."""
    img = Image.new("RGB", (200, 200), color="white")
    page = PageImage(image=img, page=1)
    result = decode_barcodes([page])
    assert result == []


def test_decode_preserves_page_number():
    """Page number from PageImage should carry through to DecodedBarcode."""
    img = Image.new("RGB", (100, 100), color="white")
    pages = [PageImage(image=img, page=3)]
    result = decode_barcodes(pages)
    for bc in result:
        assert bc.page == 3


def test_decoded_barcode_has_required_fields():
    """Any DecodedBarcode must have value, symbology, and page."""
    img = Image.new("RGB", (100, 100))
    pages = [PageImage(image=img, page=1)]
    for bc in decode_barcodes(pages):
        assert isinstance(bc.value, str)
        assert isinstance(bc.symbology, str)
        assert isinstance(bc.page, int)


def test_preprocessing_retry_path():
    """If zxing-cpp returns nothing on raw image, preprocessing retry should be attempted."""
    fake_result = type("FakeResult", (), {"text": "X001234567", "format": type("F", (), {"name": "Code128"})()})()
    call_count = 0

    def mock_zxing_decode(image):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return []  # first call (raw image) finds nothing
        return [fake_result]  # second call (preprocessed) succeeds

    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    pages = [PageImage(image=img, page=1)]

    with patch("barcode_validator.decoder._zxing_decode", side_effect=mock_zxing_decode):
        result = decode_barcodes(pages)

    assert call_count == 2, "Expected zxing_decode to be called twice (raw + preprocessed)"
    assert len(result) == 1
    assert result[0].value == "X001234567"
    assert result[0].symbology == "Code128"
    assert result[0].page == 1
