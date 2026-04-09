from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import load_images
from barcode_validator.models import BarcodeResult, BarcodeType, DecodedBarcode, LookupResult, ValidationResult
from barcode_validator.validator import validate_barcodes

if TYPE_CHECKING:
    from barcode_validator.lookup import LookupService


def decode_file(file_path: Path) -> list[DecodedBarcode]:
    """Decode all barcodes from a label proof file.

    Accepts PDF, AI, PSD, PNG, JPG, TIFF, BMP.
    Returns a list of DecodedBarcode with value, symbology, and page number.
    """
    pages = load_images(file_path)
    return decode_barcodes(pages)


def validate_label(
    file_path: str | Path,
    expected_barcodes: list[str] | None = None,
    lookup_service: LookupService | None = None,
) -> ValidationResult:
    """Validate barcodes on a label proof file.

    Decode-only mode (no expected): decodes, classifies, validates format/checkdigit.
    Comparison mode (expected provided): additionally compares against expected values.
    Lookup: when lookup_service is provided, queries public barcode databases.
    """
    path = Path(file_path)
    pages = load_images(path)
    decoded = decode_barcodes(pages)
    return validate_barcodes(decoded, str(file_path), expected_barcodes, lookup_service)


__all__ = [
    "decode_file",
    "DecodedBarcode",
    "LookupResult",
    "validate_label",
    "ValidationResult",
    "BarcodeResult",
    "BarcodeType",
]
