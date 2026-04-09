"""Barcode classifier — priority-ordered pattern matching (ADR-004)."""
import re

from barcode_validator.models import BarcodeType, DecodedBarcode


def classify(barcode: DecodedBarcode) -> BarcodeType:
    """Classify a decoded barcode by type using priority-ordered pattern matching."""
    value = barcode.value
    symbology = barcode.symbology

    # 1. FNSKU: X00 + 7 alphanumeric
    if re.match(r'^X00[A-Z0-9]{7}$', value):
        return BarcodeType.FNSKU

    # 2. ISBN-13: 13 digits with 978/979 prefix (must come before EAN-13)
    if re.match(r'^\d{13}$', value) and value[:3] in ('978', '979'):
        return BarcodeType.ISBN_13

    # 3. UPC-A: exactly 12 digits
    if re.match(r'^\d{12}$', value):
        return BarcodeType.UPC_A

    # 4. EAN-13: exactly 13 digits (non-ISBN)
    if re.match(r'^\d{13}$', value):
        return BarcodeType.EAN_13

    # 5. 8 digits: disambiguate UPC-E vs EAN-8 by symbology
    if re.match(r'^\d{8}$', value):
        if 'UPC' in symbology.upper():
            return BarcodeType.UPC_E
        return BarcodeType.EAN_8

    # 6. ASIN: B0 + 8 alphanumeric
    if re.match(r'^B0[A-Z0-9]{8}$', value):
        return BarcodeType.ASIN

    # 7. Code128 by symbology
    if 'Code128' in symbology or 'CODE128' in symbology:
        return BarcodeType.CODE128

    # 8. Code39 by symbology
    if 'Code39' in symbology or 'CODE39' in symbology:
        return BarcodeType.CODE39

    # 9. Unknown
    return BarcodeType.UNKNOWN
