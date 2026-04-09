"""Tests for CLI output formatting."""

from barcode_validator.models import BarcodeResult, BarcodeType, ValidationResult
from barcode_validator.cli_format import format_human, format_json, format_error

import json


def _make_result(
    *,
    file: str = "label_proof.pdf",
    passed: bool = True,
    mode: str = "decode",
    barcodes: list[BarcodeResult] | None = None,
    expected_not_found: list[str] | None = None,
    summary: str = "All barcodes valid.",
) -> ValidationResult:
    return ValidationResult(
        file=file,
        passed=passed,
        mode=mode,
        barcodes=barcodes or [],
        expected_not_found=expected_not_found or [],
        summary=summary,
    )


def _make_barcode(
    *,
    value: str = "0850031591271",
    barcode_type: BarcodeType = BarcodeType.EAN_13,
    symbology: str = "EAN-13",
    page: int = 1,
    valid_format: bool = True,
    valid_checkdigit: bool | None = True,
    matches_expected: bool | None = None,
) -> BarcodeResult:
    return BarcodeResult(
        value=value,
        barcode_type=barcode_type,
        symbology=symbology,
        page=page,
        valid_format=valid_format,
        valid_checkdigit=valid_checkdigit,
        matches_expected=matches_expected,
    )


class TestFormatHumanDecodeOnly:
    """format_human in decode-only mode."""

    def test_contains_file_name(self):
        result = _make_result(file="my_proof.pdf")
        output = format_human(result)
        assert "my_proof.pdf" in output

    def test_contains_mode_decode(self):
        result = _make_result(mode="decode")
        output = format_human(result)
        assert "decode" in output

    def test_contains_passed_true(self):
        result = _make_result(passed=True)
        output = format_human(result)
        assert "Passed: true" in output

    def test_contains_barcode_values_and_types(self):
        barcodes = [
            _make_barcode(value="0850031591271", barcode_type=BarcodeType.EAN_13),
            _make_barcode(
                value="X004781QUF",
                barcode_type=BarcodeType.FNSKU,
                symbology="Code-128",
                valid_checkdigit=None,
            ),
        ]
        result = _make_result(barcodes=barcodes)
        output = format_human(result)
        assert "0850031591271" in output
        assert "EAN_13" in output
        assert "X004781QUF" in output
        assert "FNSKU" in output

    def test_contains_summary(self):
        result = _make_result(summary="All barcodes valid.")
        output = format_human(result)
        assert "All barcodes valid." in output

    def test_page_in_brackets(self):
        barcodes = [_make_barcode(page=2)]
        result = _make_result(barcodes=barcodes)
        output = format_human(result)
        assert "[2]" in output


class TestFormatHumanComparisonMode:
    """format_human in comparison mode shows match status."""

    def test_shows_match_ok(self):
        barcodes = [_make_barcode(matches_expected=True)]
        result = _make_result(mode="comparison", barcodes=barcodes)
        output = format_human(result)
        assert "match: OK" in output

    def test_shows_match_fail(self):
        barcodes = [_make_barcode(matches_expected=False)]
        result = _make_result(mode="comparison", passed=False, barcodes=barcodes)
        output = format_human(result)
        assert "match: FAIL" in output


class TestFormatHumanFailed:
    """format_human with failed validation."""

    def test_passed_false(self):
        result = _make_result(passed=False, summary="Validation failed.")
        output = format_human(result)
        assert "Passed: false" in output


class TestFormatHumanEmptyBarcodes:
    """format_human with no barcodes."""

    def test_empty_barcodes_no_error(self):
        result = _make_result(barcodes=[])
        output = format_human(result)
        assert "(none)" in output


class TestFormatHumanCheckdigit:
    """format_human checkdigit display rules."""

    def test_checkdigit_none_not_shown(self):
        barcodes = [
            _make_barcode(
                value="X004781QUF",
                barcode_type=BarcodeType.FNSKU,
                valid_checkdigit=None,
            )
        ]
        result = _make_result(barcodes=barcodes)
        output = format_human(result)
        assert "checkdigit" not in output

    def test_checkdigit_true_shows_ok(self):
        barcodes = [
            _make_barcode(
                value="012345678905",
                barcode_type=BarcodeType.UPC_A,
                valid_checkdigit=True,
            )
        ]
        result = _make_result(barcodes=barcodes)
        output = format_human(result)
        assert "checkdigit: OK" in output

    def test_checkdigit_false_shows_fail(self):
        barcodes = [
            _make_barcode(
                value="012345678900",
                barcode_type=BarcodeType.UPC_A,
                valid_checkdigit=False,
            )
        ]
        result = _make_result(barcodes=barcodes)
        output = format_human(result)
        assert "checkdigit: FAIL" in output


class TestFormatJson:
    """format_json output."""

    def test_returns_valid_json(self):
        result = _make_result(barcodes=[_make_barcode()])
        output = format_json(result)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_equals_to_json(self):
        result = _make_result(barcodes=[_make_barcode()])
        assert format_json(result) == result.to_json()


class TestFormatError:
    """format_error output."""

    def test_file_not_found(self):
        err = FileNotFoundError("No such file")
        output = format_error("/tmp/missing.pdf", err)
        assert "/tmp/missing.pdf" in output
        assert "Error" in output

    def test_value_error_includes_message(self):
        err = ValueError("bad input")
        output = format_error("test.pdf", err)
        assert "bad input" in output
        assert "test.pdf" in output
