import functools

import zxingcpp
from PIL import Image

from barcode_validator.loader import PageImage
from barcode_validator.models import DecodedBarcode
from barcode_validator.preprocessing import preprocess


@functools.lru_cache
def _has_pyzbar() -> bool:
    """Check if pyzbar is available as optional fallback."""
    try:
        import pyzbar.pyzbar  # noqa: F401
        return True
    except ImportError:
        return False


def _zxing_decode(image: Image.Image) -> list[zxingcpp.Result]:
    """Decode barcodes from a PIL Image using zxing-cpp."""
    return zxingcpp.read_barcodes(image)


def _pyzbar_decode(image: Image.Image, page: int) -> list[DecodedBarcode]:
    """Decode barcodes using pyzbar as fallback."""
    from pyzbar.pyzbar import decode as pyzbar_decode

    results = pyzbar_decode(image)
    return [
        DecodedBarcode(
            value=r.data.decode("utf-8"),
            symbology=r.type,
            page=page,
        )
        for r in results
    ]


def _zxing_results_to_barcodes(
    results: list[zxingcpp.Result], page: int
) -> list[DecodedBarcode]:
    """Convert zxing-cpp results to DecodedBarcode instances."""
    return [
        DecodedBarcode(
            value=r.text,
            symbology=r.format.name,
            page=page,
        )
        for r in results
    ]


def decode_barcodes(pages: list[PageImage]) -> list[DecodedBarcode]:
    """Decode all barcodes from a list of page images.

    Strategy (ADR-001 + ADR-003):
    1. Try zxing-cpp on raw image
    2. If nothing found, preprocess (grayscale → blur → threshold) and retry zxing-cpp
    3. If still nothing and pyzbar is available, try pyzbar on raw image
    """
    all_barcodes: list[DecodedBarcode] = []

    for page_img in pages:
        barcodes = _decode_single_page(page_img)
        all_barcodes.extend(barcodes)

    return all_barcodes


def _decode_single_page(page_img: PageImage) -> list[DecodedBarcode]:
    """Decode barcodes from a single page image with retry pipeline."""
    image = page_img.image
    page = page_img.page

    # Step 1: Try zxing-cpp on raw image
    results = _zxing_decode(image)
    if results:
        return _zxing_results_to_barcodes(results, page)

    # Step 2: Preprocess and retry zxing-cpp
    preprocessed = preprocess(image)
    results = _zxing_decode(preprocessed)
    if results:
        return _zxing_results_to_barcodes(results, page)

    # Step 3: pyzbar fallback (if available)
    if _has_pyzbar():
        return _pyzbar_decode(image, page)

    return []
