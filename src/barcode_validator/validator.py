"""Orchestrator — classify, validate, and compare decoded barcodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from barcode_validator.checkdigit import validate_checkdigit
from barcode_validator.classifier import classify
from barcode_validator.comparator import match_expected
from barcode_validator.formatvalidator import validate_format
from barcode_validator.models import BarcodeResult, DecodedBarcode, ValidationResult

if TYPE_CHECKING:
    from barcode_validator.lookup import LookupService


def validate_barcodes(
    decoded: list[DecodedBarcode],
    file_path: str,
    expected_barcodes: list[str] | None = None,
    lookup_service: LookupService | None = None,
) -> ValidationResult:
    """Classify, validate, and optionally compare decoded barcodes.

    Args:
        decoded: Raw decoded barcodes from the decoder.
        file_path: Original file path (for the output).
        expected_barcodes: Expected values for comparison mode. None = decode-only.
        lookup_service: Optional lookup service for public DB queries.
    """
    mode = "comparison" if expected_barcodes is not None else "decode"

    matches_dict: dict[str, bool] = {}
    not_found: list[str] = []
    if expected_barcodes is not None:
        matches_dict, not_found = match_expected(
            [b.value for b in decoded], expected_barcodes
        )

    results: list[BarcodeResult] = []
    for barcode in decoded:
        barcode_type = classify(barcode)
        valid_format = validate_format(barcode.value, barcode_type)
        valid_checkdigit = validate_checkdigit(barcode.value, barcode_type)
        matches_expected = (
            matches_dict.get(barcode.value, False)
            if expected_barcodes is not None
            else None
        )
        lookup_result = None
        if lookup_service is not None:
            lookup_result = lookup_service.lookup(barcode.value, barcode_type)
        results.append(
            BarcodeResult(
                value=barcode.value,
                barcode_type=barcode_type,
                symbology=barcode.symbology,
                page=barcode.page,
                valid_format=valid_format,
                valid_checkdigit=valid_checkdigit,
                matches_expected=matches_expected,
                lookup=lookup_result,
            )
        )

    if mode == "decode":
        passed = bool(results) and all(
            b.valid_format and b.valid_checkdigit is not False for b in results
        )
    else:
        passed = len(not_found) == 0 and all(
            b.matches_expected for b in results if b.matches_expected is not None
        )

    count = len(results)
    verdict = "All validations passed." if passed else "Validation failed."
    summary = f"{count} barcode(s) found. {verdict}"

    return ValidationResult(
        file=file_path,
        passed=passed,
        mode=mode,
        barcodes=results,
        expected_not_found=not_found,
        summary=summary,
    )
