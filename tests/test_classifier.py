"""Tests for barcode classifier — priority-ordered pattern matching (ADR-004)."""
from barcode_validator.classifier import classify
from barcode_validator.models import BarcodeType, DecodedBarcode


def _barcode(value: str, symbology: str, page: int = 1) -> DecodedBarcode:
    return DecodedBarcode(value=value, symbology=symbology, page=page)


def test_classify_fnsku():
    result = classify(_barcode("X004781QUF", "Code128"))
    assert result is BarcodeType.FNSKU


def test_classify_isbn13():
    result = classify(_barcode("9780134685991", "EAN13"))
    assert result is BarcodeType.ISBN_13


def test_classify_upca():
    result = classify(_barcode("012345678905", "UPCA"))
    assert result is BarcodeType.UPC_A


def test_classify_ean13():
    result = classify(_barcode("4006381333931", "EAN13"))
    assert result is BarcodeType.EAN_13


def test_classify_ean8():
    result = classify(_barcode("96385074", "EAN8"))
    assert result is BarcodeType.EAN_8


def test_classify_upce():
    result = classify(_barcode("01234565", "UPCE"))
    assert result is BarcodeType.UPC_E


def test_classify_8digit_ean_symbology():
    result = classify(_barcode("12345670", "EAN8"))
    assert result is BarcodeType.EAN_8


def test_classify_8digit_upc_symbology():
    result = classify(_barcode("12345670", "UPCE"))
    assert result is BarcodeType.UPC_E


def test_classify_asin():
    result = classify(_barcode("B08N5WRWNW", "Code128"))
    assert result is BarcodeType.ASIN


def test_classify_generic_code128():
    result = classify(_barcode("HELLO123", "Code128"))
    assert result is BarcodeType.CODE128


def test_classify_code39():
    result = classify(_barcode("HELLO123", "Code39"))
    assert result is BarcodeType.CODE39


def test_classify_unknown():
    result = classify(_barcode("SOMETHING", "SomeWeirdFormat"))
    assert result is BarcodeType.UNKNOWN


def test_classify_isbn_before_ean():
    """ISBN-13 must match before EAN-13 (both are 13 digits, but 978/979 prefix wins)."""
    result = classify(_barcode("9781234567890", "EAN13"))
    assert result is BarcodeType.ISBN_13


def test_classify_fnsku_before_code128():
    """FNSKU must match before Code128 (pattern takes priority over symbology)."""
    result = classify(_barcode("X004781QUF", "Code128"))
    assert result is BarcodeType.FNSKU
