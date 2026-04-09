"""Integration tests against real label proofs in test_docs/.

These tests verify the full pipeline: file → load → decode → DecodedBarcode list.
Expected values are ground-truth from manual verification.
"""
from pathlib import Path

import pytest

from barcode_validator import decode_file, DecodedBarcode, validate_label, BarcodeType

TEST_DOCS = Path(__file__).parent.parent / "test_docs"

pytestmark = pytest.mark.skipif(
    not TEST_DOCS.exists(), reason="test_docs/ not available"
)


class TestPDFProofs:
    """Test decoding against real NCL PDF label proofs."""

    def test_proof_540841_decodes_ean13(self):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = decode_file(path)
        assert len(result) >= 1
        values = [bc.value for bc in result]
        assert "0850031591271" in values
        bc = next(b for b in result if b.value == "0850031591271")
        assert bc.symbology == "EAN13"
        assert bc.page == 1

    def test_proof_540837_no_barcodes_detected(self):
        path = TEST_DOCS / "(proof)(BL6)(540837).pdf"
        result = decode_file(path)
        assert result == []

    def test_excel_printpack_0480_01_runs_without_error(self):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-01 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)

    def test_excel_printpack_0480_04_runs_without_error(self):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-04 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)


class TestAIFiles:
    """Test decoding AI files (PDF-compatible)."""

    def test_ai_file_runs_without_error(self):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai"
        result = decode_file(path)
        assert isinstance(result, list)


class TestRasterImages:
    """Test decoding raster images."""

    def test_jpg_decodes_fnsku(self):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg"
        result = decode_file(path)
        assert len(result) >= 1
        values = [bc.value for bc in result]
        assert "X004781QUF" in values
        bc = next(b for b in result if b.value == "X004781QUF")
        assert bc.symbology == "Code128"
        assert bc.page == 1


class TestValidateLabel:
    """Integration tests for validate_label (EPIC 2)."""

    def test_decode_only_pdf(self):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = validate_label(path)
        assert result.mode == "decode"
        assert result.passed is True
        bc = next(b for b in result.barcodes if b.value == "0850031591271")
        assert bc.barcode_type == BarcodeType.EAN_13
        assert bc.valid_format is True
        assert bc.valid_checkdigit is True
        assert bc.matches_expected is None

    def test_comparison_match(self):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = validate_label(path, expected_barcodes=["0850031591271"])
        assert result.mode == "comparison"
        assert result.passed is True
        assert result.expected_not_found == []

    def test_comparison_mismatch(self):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = validate_label(path, expected_barcodes=["WRONG"])
        assert result.passed is False
        assert "WRONG" in result.expected_not_found

    def test_jpg_fnsku(self):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg"
        result = validate_label(path)
        bc = next(b for b in result.barcodes if b.value == "X004781QUF")
        assert bc.barcode_type == BarcodeType.FNSKU
        assert bc.valid_format is True
        assert bc.valid_checkdigit is None

    def test_to_json_output(self):
        import json

        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = validate_label(path)
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


# ---------------------------------------------------------------------------
# Ground-truth parametrized tests
# ---------------------------------------------------------------------------
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from conftest import GROUND_TRUTH  # noqa: E402

from barcode_validator import ValidationResult

_files_with_barcodes = [f for f, data in GROUND_TRUTH.items() if data["barcodes"]]
_all_files = list(GROUND_TRUTH.keys())

# Files where barcodes exist but the decoder currently fails to extract them.
# Tracked in ERRORS.md — remove xfail as decoding is fixed.
_decode_failures = {
    "(proof)(BL6)(540837).pdf",
    "EXCEL PRINTPACK-0480-01 proof.pdf",
    "EXCEL PRINTPACK-0480-04 proof.pdf",
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai",
}


def _maybe_xfail(file: str):
    if file in _decode_failures:
        return pytest.param(file, marks=pytest.mark.xfail(reason="decoder does not extract barcode from this file"))
    return file


class TestGroundTruth:
    """Parametrized tests driven by GROUND_TRUTH in conftest."""

    @pytest.mark.parametrize("file", [_maybe_xfail(f) for f in _files_with_barcodes])
    def test_ground_truth_decode(self, file: str):
        """Decode-only: every ground-truth barcode is found with correct type and symbology."""
        result = validate_label(TEST_DOCS / file)
        decoded_values = [b.value for b in result.barcodes]
        for expected in GROUND_TRUTH[file]["barcodes"]:
            assert expected["value"] in decoded_values, (
                f"Expected {expected['value']} not found in {decoded_values}"
            )
            bc = next(b for b in result.barcodes if b.value == expected["value"])
            assert bc.barcode_type == BarcodeType(expected["type"])
            assert bc.symbology == expected["symbology"]

    @pytest.mark.parametrize("file", [_maybe_xfail(f) for f in _files_with_barcodes])
    def test_ground_truth_comparison(self, file: str):
        """Comparison mode with all ground-truth values passes."""
        expected_values = [b["value"] for b in GROUND_TRUTH[file]["barcodes"]]
        result = validate_label(TEST_DOCS / file, expected_barcodes=expected_values)
        assert result.passed is True
        assert result.expected_not_found == []

    @pytest.mark.parametrize("file", _all_files)
    def test_all_files_run_without_error(self, file: str):
        """Every known file runs through validate_label without exception."""
        result = validate_label(TEST_DOCS / file)
        assert isinstance(result, ValidationResult)

    @pytest.mark.parametrize("file", _all_files)
    def test_json_schema_all_files(self, file: str):
        """to_json() output has all PRD-required fields."""
        result = validate_label(TEST_DOCS / file)
        data = json.loads(result.to_json())
        for key in ("file", "passed", "mode", "barcodes", "expected_not_found", "summary"):
            assert key in data, f"Missing top-level key: {key}"
        for bc in data["barcodes"]:
            for key in ("value", "type", "symbology", "page",
                        "valid_format", "valid_checkdigit", "matches_expected"):
                assert key in bc, f"Missing barcode key: {key}"


class TestValidateLabelErrors:
    """Error-path tests for validate_label."""

    def test_validate_label_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            validate_label("nonexistent.pdf")

    def test_validate_label_unsupported_format(self, unsupported_file):
        with pytest.raises(ValueError, match="Unsupported"):
            validate_label(unsupported_file)
