import json

from barcode_validator.models import (
    BarcodeResult,
    BarcodeType,
    DecodedBarcode,
    ValidationResult,
)


def test_decoded_barcode_fields():
    bc = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert bc.value == "X001234567"
    assert bc.symbology == "CODE128"
    assert bc.page == 1


def test_decoded_barcode_equality():
    a = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    b = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert a == b


# --- BarcodeType enum ---


def test_barcode_type_has_all_values():
    expected = {
        "FNSKU", "ISBN_13", "UPC_A", "EAN_13", "EAN_8",
        "UPC_E", "ASIN", "CODE128", "CODE39", "UNKNOWN",
    }
    actual = {member.name for member in BarcodeType}
    assert actual == expected


def test_barcode_type_values():
    assert BarcodeType.FNSKU.value == "FNSKU"
    assert BarcodeType.ISBN_13.value == "ISBN_13"
    assert BarcodeType.UPC_A.value == "UPC_A"
    assert BarcodeType.EAN_13.value == "EAN_13"
    assert BarcodeType.EAN_8.value == "EAN_8"
    assert BarcodeType.UPC_E.value == "UPC_E"
    assert BarcodeType.ASIN.value == "ASIN"
    assert BarcodeType.CODE128.value == "CODE128"
    assert BarcodeType.CODE39.value == "CODE39"
    assert BarcodeType.UNKNOWN.value == "UNKNOWN"


# --- BarcodeResult ---


def test_barcode_result_fields():
    br = BarcodeResult(
        value="X001ABC123",
        barcode_type=BarcodeType.FNSKU,
        symbology="CODE128",
        page=1,
        valid_format=True,
        valid_checkdigit=None,
        matches_expected=True,
    )
    assert br.value == "X001ABC123"
    assert br.barcode_type == BarcodeType.FNSKU
    assert br.symbology == "CODE128"
    assert br.page == 1
    assert br.valid_format is True
    assert br.valid_checkdigit is None
    assert br.matches_expected is True


def test_barcode_result_frozen():
    br = BarcodeResult(
        value="012345678905",
        barcode_type=BarcodeType.UPC_A,
        symbology="EAN13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
    )
    import pytest
    with pytest.raises(AttributeError):
        br.value = "changed"


# --- ValidationResult ---


def _make_validation_result() -> ValidationResult:
    barcode = BarcodeResult(
        value="X001ABC123",
        barcode_type=BarcodeType.FNSKU,
        symbology="CODE128",
        page=1,
        valid_format=True,
        valid_checkdigit=None,
        matches_expected=True,
    )
    return ValidationResult(
        file="label_proof.pdf",
        passed=True,
        mode="comparison",
        barcodes=[barcode],
        expected_not_found=[],
        summary="1 barcode found. All validations passed.",
    )


def test_validation_result_to_dict_shape():
    vr = _make_validation_result()
    d = vr.to_dict()
    assert d["file"] == "label_proof.pdf"
    assert d["passed"] is True
    assert d["mode"] == "comparison"
    assert d["summary"] == "1 barcode found. All validations passed."
    assert isinstance(d["barcodes"], list)
    assert isinstance(d["expected_not_found"], list)


def test_validation_result_to_dict_barcode_type_key():
    """barcode_type serializes as 'type' in JSON output per PRD."""
    vr = _make_validation_result()
    d = vr.to_dict()
    bc = d["barcodes"][0]
    assert "type" in bc
    assert "barcode_type" not in bc
    assert bc["type"] == "FNSKU"


def test_validation_result_to_dict_barcodes_are_dicts():
    vr = _make_validation_result()
    d = vr.to_dict()
    assert all(isinstance(b, dict) for b in d["barcodes"])


def test_validation_result_to_dict_expected_not_found_strings():
    barcode = BarcodeResult(
        value="X001ABC123",
        barcode_type=BarcodeType.FNSKU,
        symbology="CODE128",
        page=1,
        valid_format=True,
        valid_checkdigit=None,
        matches_expected=False,
    )
    vr = ValidationResult(
        file="label.pdf",
        passed=False,
        mode="comparison",
        barcodes=[barcode],
        expected_not_found=["X009MISSING"],
        summary="Expected barcode not found.",
    )
    d = vr.to_dict()
    assert d["expected_not_found"] == ["X009MISSING"]
    assert all(isinstance(s, str) for s in d["expected_not_found"])


def test_validation_result_to_json_valid():
    vr = _make_validation_result()
    j = vr.to_json()
    parsed = json.loads(j)
    assert parsed["file"] == "label_proof.pdf"


def test_validation_result_null_checkdigit_in_json():
    """valid_checkdigit=None must serialize to JSON null."""
    vr = _make_validation_result()
    j = vr.to_json()
    parsed = json.loads(j)
    assert parsed["barcodes"][0]["valid_checkdigit"] is None


def test_validation_result_null_matches_expected_in_json():
    """matches_expected=None must serialize to JSON null."""
    barcode = BarcodeResult(
        value="012345678905",
        barcode_type=BarcodeType.UPC_A,
        symbology="EAN13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
    )
    vr = ValidationResult(
        file="test.pdf",
        passed=True,
        mode="decode",
        barcodes=[barcode],
        expected_not_found=[],
        summary="1 barcode found.",
    )
    j = vr.to_json()
    parsed = json.loads(j)
    assert parsed["barcodes"][0]["matches_expected"] is None
