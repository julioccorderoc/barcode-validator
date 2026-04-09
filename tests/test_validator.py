"""Tests for the validator orchestrator."""
import json

import pytest

from barcode_validator.models import BarcodeType, DecodedBarcode
from barcode_validator.validator import validate_barcodes


class TestValidateBarcodes:
    """Unit tests for validate_barcodes."""

    def test_validate_decode_only_mode(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf")
        assert result.mode == "decode"
        assert all(b.matches_expected is None for b in result.barcodes)

    def test_validate_comparison_mode(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf", expected_barcodes=["X004781QUF"])
        assert result.mode == "comparison"

    def test_validate_decode_only_passed_valid_fnsku(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf")
        assert result.passed is True
        bc = result.barcodes[0]
        assert bc.barcode_type == BarcodeType.FNSKU
        assert bc.valid_format is True
        assert bc.valid_checkdigit is None

    def test_validate_decode_only_failed_invalid_checkdigit(self):
        # 0850031591270 has a corrupted check digit (correct is ...1271)
        decoded = [DecodedBarcode("0850031591270", "EAN13", 1)]
        result = validate_barcodes(decoded, "test.pdf")
        assert result.passed is False
        bc = result.barcodes[0]
        assert bc.barcode_type == BarcodeType.EAN_13
        assert bc.valid_checkdigit is False

    def test_validate_comparison_all_matched(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf", expected_barcodes=["X004781QUF"])
        assert result.passed is True
        assert result.expected_not_found == []

    def test_validate_comparison_missing_expected(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf", expected_barcodes=["MISSING"])
        assert result.passed is False
        assert "MISSING" in result.expected_not_found

    def test_validate_empty_decoded_decode_only(self):
        result = validate_barcodes([], "test.pdf")
        assert result.passed is True
        assert "0" in result.summary

    def test_validate_empty_decoded_comparison(self):
        result = validate_barcodes([], "test.pdf", expected_barcodes=["A"])
        assert result.passed is False

    def test_validate_to_json_schema(self):
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(decoded, "test.pdf")
        data = json.loads(result.to_json())
        assert "file" in data
        assert "passed" in data
        assert "mode" in data
        assert "barcodes" in data
        assert "expected_not_found" in data
        assert "summary" in data
        for bc in data["barcodes"]:
            assert "type" in bc
            assert "value" in bc
            assert "symbology" in bc
            assert "page" in bc
            assert "valid_format" in bc
            assert "valid_checkdigit" in bc
            assert "matches_expected" in bc

    def test_validate_file_field(self):
        result = validate_barcodes([], "/path/to/file.pdf")
        assert result.file == "/path/to/file.pdf"
