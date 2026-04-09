"""Format validation for barcode values against expected patterns."""
import re

from barcode_validator.models import BarcodeType

_FORMAT_PATTERNS: dict[BarcodeType, re.Pattern[str]] = {
    BarcodeType.FNSKU: re.compile(r"^X00[A-Z0-9]{7}$"),
    BarcodeType.ISBN_13: re.compile(r"^(978|979)\d{10}$"),
    BarcodeType.UPC_A: re.compile(r"^\d{12}$"),
    BarcodeType.EAN_13: re.compile(r"^\d{13}$"),
    BarcodeType.EAN_8: re.compile(r"^\d{8}$"),
    BarcodeType.UPC_E: re.compile(r"^\d{8}$"),
    BarcodeType.ASIN: re.compile(r"^B0[A-Z0-9]{8}$"),
    BarcodeType.CODE128: re.compile(r"^[\x20-\x7E]+$"),
    BarcodeType.CODE39: re.compile(r"^[A-Z0-9 \-.$/+%]+$"),
    BarcodeType.UNKNOWN: re.compile(r"^.+$"),
}


def validate_format(value: str, barcode_type: BarcodeType) -> bool:
    """Validate barcode value matches expected format regex for its type."""
    pattern = _FORMAT_PATTERNS.get(barcode_type)
    if pattern is None:
        return False
    return pattern.match(value) is not None
