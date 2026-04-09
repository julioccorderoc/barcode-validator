from dataclasses import dataclass
from enum import Enum
import json


@dataclass(frozen=True)
class DecodedBarcode:
    """A single barcode decoded from an image."""
    value: str
    symbology: str
    page: int


class BarcodeType(Enum):
    """Classification of barcode types supported by the validator."""
    FNSKU = "FNSKU"
    ISBN_13 = "ISBN_13"
    UPC_A = "UPC_A"
    EAN_13 = "EAN_13"
    EAN_8 = "EAN_8"
    UPC_E = "UPC_E"
    ASIN = "ASIN"
    CODE128 = "CODE128"
    CODE39 = "CODE39"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LookupResult:
    """Product information from a public barcode database."""
    found: bool
    product_name: str | None
    brand: str | None
    category: str | None
    source: str | None


@dataclass(frozen=True)
class BarcodeResult:
    """A classified and validated barcode."""
    value: str
    barcode_type: BarcodeType
    symbology: str
    page: int
    valid_format: bool
    valid_checkdigit: bool | None
    matches_expected: bool | None
    lookup: LookupResult | None = None


@dataclass
class ValidationResult:
    """Final validation output for a file."""
    file: str
    passed: bool
    mode: str
    barcodes: list[BarcodeResult]
    expected_not_found: list[str]
    summary: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "passed": self.passed,
            "mode": self.mode,
            "barcodes": [
                {
                    "value": b.value,
                    "type": b.barcode_type.value,
                    "symbology": b.symbology,
                    "page": b.page,
                    "valid_format": b.valid_format,
                    "valid_checkdigit": b.valid_checkdigit,
                    "matches_expected": b.matches_expected,
                    "lookup": {
                        "found": b.lookup.found,
                        "product_name": b.lookup.product_name,
                        "brand": b.lookup.brand,
                        "category": b.lookup.category,
                        "source": b.lookup.source,
                    } if b.lookup is not None else None,
                }
                for b in self.barcodes
            ],
            "expected_not_found": list(self.expected_not_found),
            "summary": self.summary,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
