# PDF/Image to Barcode Extraction Pipeline

> Research 2026-04-09. Self-contained label proof validation.

---

## 1. PDF to Image

| Library | System Deps | Speed | Self-Contained |
| ------- | ----------- | ----- | -------------- |
| PyMuPDF (fitz) | None | 300+ pps | Yes |
| pypdfium2 | None | 200-250 pps | Yes |
| pdf2image | Poppler | 60-100 pps | No |
| pikepdf | None | N/A | Yes (images only) |

**PyMuPDF (recommended):** MuPDF engine bundled. 300+ pps, ~3ms/page. Renders pages to Pillow images, clips regions, extracts text. `pip install PyMuPDF`

**pypdfium2:** Google PDFium. Good alternative, lighter. `pip install pypdfium2`

**pdf2image:** Needs Poppler system lib. 3-5x slower. Not self-contained.

**pikepdf:** Only extracts embedded rasters. Can't render vector barcodes. Not suitable.

---

## 2. Image Preprocessing

### Pipeline

```text
Image → Grayscale → Gaussian Blur (5x5) → Otsu Threshold → Decode
```

### Steps

1. **Grayscale** — 3 channels to 1, faster
2. **Gaussian blur** — reduces noise (5x5 or 7x7)
3. **Otsu threshold** — auto optimal binary threshold
4. **Morphological ops** — cleans small artifacts
5. **Unsharp mask** — boosts edge contrast (optional, low-quality only)

### Rotation/Skew

- OpenCV 4.x `BarcodeDetector` handles skew auto
- Manual: contour analysis → `minAreaRect` → skew angle → `warpAffine`
- pyzbar handles moderate rotation

### Multi-Barcode

- pyzbar: 85% success
- zxing-cpp: single barcode per image (v3 has `read_barcodes()`)
- Strategy: pyzbar primary; crop candidates via contour analysis if needed

---

## 3. End-to-End Pipeline

```text
PDF → PyMuPDF 2x render → OpenCV preprocess → pyzbar decode → classify → validate → report
```

### Example

```python
import fitz
from pyzbar.pyzbar import decode
import cv2
import numpy as np
from PIL import Image

def extract_barcodes_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    results = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
        cv_img = cv2.GaussianBlur(cv_img, (5, 5), 0)
        _, binary = cv2.threshold(cv_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
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

- FNSKU barcode (Code 128) = primary scannable
- Size: 1"x2" to 2"x3"
- **One barcode visible per item.** FNSKU must cover manufacturer barcode. Two visible = rejection.

### Proof Validation Checks

1. FNSKU present and scannable
2. Value matches expected
3. Code 128 symbology
4. No conflicting extra barcodes
5. Text matches product info (optional OCR)

---

## 5. Performance

| Step | Time |
| ---- | ---- |
| PDF render | ~3 ms/page |
| Preprocess | ~5 ms/image |
| Decode | ~50-100 ms/image |
| **Total** | **~60-110 ms/page** |

Memory: ~25 MB per A4 at 300 DPI RGB. Batch: process one page at a time. Standard laptop sufficient, 4 GB RAM min, no GPU.

---

## 6. Dependencies

```text
PyMuPDF          # PDF render (self-contained)
pyzbar           # Decode (needs zbar: brew install zbar / apt install libzbar0)
opencv-python    # Preprocessing
Pillow           # Image handling
numpy            # Arrays (via OpenCV)
```

Self-contained alt: replace pyzbar with zxing-cpp. Trade-off: worse multi-barcode, zero system deps.

---

## Sources

- [PyMuPDF docs](https://pymupdf.readthedocs.io/en/latest/)
- [pypdfium2 GitHub](https://github.com/pypdfium2-team/pypdfium2)
- [OpenCV barcode tutorial](https://docs.opencv.org/4.x/d6/d25/tutorial_barcode_detect_and_decode.html)
- [Amazon FBA barcode requirements](https://sellercentral.amazon.com/gp/help/external/G201100910)
