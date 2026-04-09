from barcode_validator.models import DecodedBarcode


def test_decoded_barcode_fields():
    bc = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert bc.value == "X001234567"
    assert bc.symbology == "CODE128"
    assert bc.page == 1


def test_decoded_barcode_equality():
    a = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    b = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert a == b
