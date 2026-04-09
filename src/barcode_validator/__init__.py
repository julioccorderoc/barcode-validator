from pathlib import Path

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import load_images
from barcode_validator.models import DecodedBarcode


def decode_file(file_path: Path) -> list[DecodedBarcode]:
    """Decode all barcodes from a label proof file.

    Accepts PDF, AI, PSD, PNG, JPG, TIFF, BMP.
    Returns a list of DecodedBarcode with value, symbology, and page number.
    """
    pages = load_images(file_path)
    return decode_barcodes(pages)


__all__ = ["decode_file", "DecodedBarcode"]
