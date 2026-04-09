# PDF/Image to Barcode Extraction Pipeline

> Research conducted 2026-04-09. Focus: self-contained solutions for label proof validation.

---

## 1. PDF to Image Conversion

### Comparison

| Library | System Deps | Speed | Self-Contained | Notes |
|---------|-------------|-------|----------------|-------|
| **PyMuPDF (fitz)** | None | 300+ pages/sec | Yes | Fastest, bundled deps |
| **pypdfium2** | None | 200-250 pages/sec | Yes | Lightweight, Google PDFium |
| **pdf2image** | Poppler | 60-100 pages/sec | No | Mature but external dep |
| **pikepdf** | None | N/A | Yes | Extracts embedded images only |

### PyMuPDF (fitz) — Recommended

- Direct binding to MuPDF rendering engine
- Renders pages to Pillow images, can clip specific regions
- No external system dependencies (bundled with pip package)
- **300+ pages/second** (PyMuPDF 1.26.7)
- `pip install PyMuPDF`

### pypdfium2 — Good Alternative

- Python binding to Google's PDFium renderer
- No system dependencies, cross-platform wheels
- Lighter than PyMuPDF
- `pip install pypdfium2`

### pdf2image / Poppler — Not Recommended for Self-Contained

- Requires Poppler system library (`brew install poppler`, `apt install poppler-utils`)
- 3-5x slower than PyMuPDF
- Not suitable for containerized/isolated deployments

### pikepdf — Not Suitable

- Only extracts embedded raster images from PDFs
- Cannot render vector content (printed barcode labels are typically vector)
- Cannot handle barcodes rendered via PDF drawing commands

---

## 2. Image Preprocessing for Barcode Detection

### Standard Pipeline

```text
Image → Grayscale → Gaussian Blur → Otsu Threshold → Barcode Decode
```

### Steps That Improve Detection

1. **Grayscale conversion** — Reduces 3 channels to 1, improves speed
2. **Gaussian blur** — Reduces noise (5x5 or 7x7 kernel)
3. **Otsu's thresholding** — Automatically determines optimal threshold from histogram
4. **Morphological operations** — Cleans up small noise artifacts
5. **Unsharp masking** — Boosts edge contrast (optional, for low-quality images)

### Handling Rotated/Skewed Barcodes

- OpenCV 4.x `BarcodeDetector` handles skew automatically
- Manual approach: analyze contours with `minAreaRect`, find skew angle, apply `warpAffine`
- pyzbar handles moderate rotation well

### Handling Multiple Barcodes

- **pyzbar:** Excellent (85% success rate on multi-barcode images)
- **zxing-cpp:** Poor (only reads one barcode per image)
- **Strategy:** Use pyzbar as primary; if needed, crop candidate regions via contour analysis

---

## 3. End-to-End Pipeline

### Recommended Architecture

```text
PDF label proof
    ↓
PyMuPDF (render page to image at 2x scale / 300 DPI)
    ↓
OpenCV preprocessing (grayscale → blur → Otsu threshold)
    ↓
pyzbar (decode all barcodes on page)
    ↓
Classify barcode type (UPC/EAN/FNSKU/ASIN by regex)
    ↓
Validate (check digit, format, match against expected value)
    ↓
Report (pass/fail with details)
```

### Example Code

```python
import fitz  # PyMuPDF
from pyzbar.pyzbar import decode
import cv2
import numpy as np
from PIL import Image

def extract_barcodes_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    results = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        # Render at 2x scale for better barcode detection
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Preprocess with OpenCV
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        cv_img = cv2.GaussianBlur(cv_img, (5, 5), 0)
        _, binary = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Decode barcodes (try both original and preprocessed)
        barcodes = decode(img) or decode(Image.fromarray(binary))
        for bc in barcodes:
            results.append({
                'page': page_num + 1,
                'data': bc.data.decode('utf-8'),
                'type': bc.type,
                'rect': bc.rect,
            })

    doc.close()
    return results
```

---

## 4. Amazon FBA Label Specifics

### What Labels Look Like

- FNSKU barcode (Code 128) — primary scannable barcode
- Product title/description text
- Condition label (if applicable)
- Size: typically 1"×2" to 2"×3"

### Critical Rule

**Only one barcode should be visible per item.** FNSKU must cover any existing manufacturer barcode. Two visible barcodes = Amazon rejection.

### For Label Proof Validation

When validating a label proof before printing, check:

1. FNSKU barcode is present and scannable
2. Decoded value matches expected FNSKU
3. Barcode is Code 128 symbology
4. No conflicting/extra barcodes visible
5. Text matches expected product info (optional OCR step)

---

## 5. Performance

### Processing Speed (Single Document)

- PDF render: ~3ms per page (PyMuPDF at 2x scale)
- Preprocessing: ~5ms per image (OpenCV)
- Barcode decode: ~50-100ms per image (pyzbar)
- **Total: ~60-110ms per page** — well under 1 second

### Memory

- Single A4 page at 300 DPI RGB: ~25 MB
- Manageable for single-document label proof validation
- For batch: process one page at a time, release memory

### Hardware Requirements

- Standard laptop/desktop: more than sufficient
- 4 GB RAM minimum
- No GPU required

---

## 6. Required Dependencies

### Python Packages

```text
PyMuPDF          # PDF rendering (self-contained)
pyzbar           # Barcode decoding
opencv-python    # Image preprocessing (opencv-contrib-python for BarcodeDetector)
Pillow           # Image handling
numpy            # Array operations (pulled in by OpenCV)
```

### System Dependencies

- **pyzbar requires zbar:**
  - macOS: `brew install zbar`
  - Linux: `apt install libzbar0`
  - Windows: bundled with wheel (no action needed)

### Fully Self-Contained Alternative

If system deps are unacceptable, replace pyzbar with `zxing-cpp` (`pip install zxing-cpp`). Trade-off: worse multi-barcode handling but zero system dependencies.

---

## Sources

- [PyMuPDF documentation](https://pymupdf.readthedocs.io/en/latest/)
- [pypdfium2 GitHub](https://github.com/pypdfium2-team/pypdfium2)
- [OpenCV barcode tutorial](https://docs.opencv.org/4.x/d6/d25/tutorial_barcode_detect_and_decode.html)
- [pyzbar PyPI](https://pypi.org/project/pyzbar/)
- [Dynamsoft benchmark](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
- [Amazon FBA barcode requirements](https://sellercentral.amazon.com/gp/help/external/G201100910)
