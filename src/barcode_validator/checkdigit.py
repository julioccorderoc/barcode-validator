"""Check digit validation for barcode values."""

from barcode_validator.models import BarcodeType


def _mod10_check(digits: str) -> bool:
    """MOD 10 (GTIN) check digit validation.

    Starting from the rightmost digit, alternate weights of 1 and 3.
    Valid if the weighted sum is divisible by 10.
    """
    total = 0
    for i, ch in enumerate(reversed(digits)):
        weight = 1 if i % 2 == 0 else 3
        total += int(ch) * weight
    return total % 10 == 0


_CHECKDIGIT_TYPES: set[BarcodeType] = {
    BarcodeType.UPC_A,
    BarcodeType.EAN_13,
    BarcodeType.EAN_8,
    BarcodeType.ISBN_13,
    BarcodeType.UPC_E,
}


def validate_checkdigit(value: str, barcode_type: BarcodeType) -> bool | None:
    """Validate check digit for the given barcode value and type.

    Returns True if valid, False if invalid, None if type has no check digit.
    """
    if barcode_type not in _CHECKDIGIT_TYPES:
        return None
    return _mod10_check(value)
