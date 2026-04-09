from dataclasses import dataclass


@dataclass(frozen=True)
class DecodedBarcode:
    """A single barcode decoded from an image."""
    value: str
    symbology: str
    page: int
