# Barcode Reading Libraries for Python

> Research conducted 2026-04-09. Focus: self-contained solutions, no external APIs.

## Summary

| Library | License | Barcode Types | Multi-Barcode | System Deps | Active | Accuracy |
|---------|---------|---------------|---------------|-------------|--------|----------|
| **pyzbar** | MIT + LGPL | EAN/UPC/Code128/Code39/QR | Good (85%) | zbar C lib | Inactive | 71.2% |
| **zxing-cpp** | Apache 2.0 | Extensive 1D/2D | Poor (23.8%) | None | Active | 65.9% |
| **pyzxing** | Open | Extensive 1D/2D | One only | Java/JVM | Low | N/A |
| **OpenCV** | BSD | EAN only | N/A | None | Active | N/A |
| **Dynamsoft** | Commercial | Extensive | Good | None | Active | 90.6% |
| **pylibdmtx** | Open | Data Matrix only | Good | libdmtx | Low | N/A |

---

## 1. pyzbar (python-zbar)

Wrapper around the ZBar C library for reading 1D barcodes and QR codes.

**Supported Barcode Types:**

- EAN-13, EAN-8, UPC-A, UPC-E
- Code 128, Code 93, Code 39
- Codabar, Interleaved 2 of 5
- QR Code

**License:** MIT (wrapper) + GNU LGPL v2.1 (zbar lib)

**System Dependencies:**

- Requires zbar shared library
- Windows: DLLs included with wheel
- macOS: `brew install zbar`
- Linux: `sudo apt-get install libzbar0`

**Installation:** `pip install pyzbar`

**Image Support:** PIL/Pillow images, OpenCV arrays, NumPy ndarrays, raw bytes

**Maintenance:** Inactive (no releases in 12+ months), but 112K weekly downloads

**Accuracy:** 71.2% on 170 real-world production images. Multi-barcode: 85% success rate.

**Verdict:** Best balance of accuracy, multi-barcode support, and barcode type coverage. Stable underlying C library despite inactive Python wrapper.

---

## 2. python-barcode

**GENERATION ONLY** — does NOT decode/read barcodes. Not suitable for this use case.

---

## 3. zxing-cpp (Python wrapper)

C++ port of ZXing with Python bindings.

**Supported Barcode Types:**

- 1D: Codabar, Code39, Code93, Code128, EAN8, EAN13, ITF, UPC-A, UPC-E, DataBar
- 2D: QR Code, Micro QR, rMQR, Aztec, Data Matrix, PDF417, MaxiCode

**License:** Apache 2.0

**System Dependencies:** None (pure C++ with Python wheels)

**Installation:** `pip install zxing-cpp`

**Performance:** Fastest detection (40.2 ms avg), but only 65.9% accuracy on diverse real-world images. Multi-barcode: 23.8% success on messy images (but `read_barcodes()` API now available in v3.0.0).

**Update (Apr 2026):** v3.0.0 released Feb 2026. Now includes `read_barcodes()` for multi-barcode detection. Supports Python 3.10-3.14. Actively maintained.

**Verdict:** Best choice for self-contained deployments — zero system deps, active maintenance, broad format support. Multi-barcode accuracy still trails pyzbar on messy images, but likely sufficient for clean label proofs.

---

## 4. pyzxing (Java wrapper)

Python wrapper calling ZXing Java library via subprocess.

**System Dependencies:** Requires Java/JVM (OpenJDK 8+). Downloads JAR at runtime.

**Verdict:** Not recommended — zxing-cpp is better in every way without the Java dependency.

---

## 5. OpenCV (cv2.barcode module)

Native barcode detection in OpenCV 4.6.0+.

**Supported:** EAN-8, EAN-13, UPC-A, UPC-E only. Does NOT support Code128, Code39.

**Installation:** `pip install opencv-contrib-python` (requires contrib version)

**Verdict:** Insufficient barcode format coverage for production. Best used for **image preprocessing** before passing to pyzbar/zxing.

---

## 6. Dynamsoft Barcode Reader

**Commercial** — not free/open source. Best accuracy (90.6%) but requires paid license.

---

## 7. pylibdmtx

Reads **Data Matrix barcodes only**. Requires libdmtx system library.

**Verdict:** Niche — only useful if Data Matrix barcodes are in scope.

---

## Recommendation

**Best approach for self-contained label validation:**

1. **Primary decoder:** `pyzbar` — best accuracy + multi-barcode support
2. **Preprocessing:** `OpenCV` — grayscale, blur, thresholding to improve detection
3. **Fallback decoder:** `zxing-cpp` — broader format support, no system deps, useful as secondary attempt

**Hybrid strategy:** Try pyzbar first (better accuracy), fall back to zxing-cpp if pyzbar fails or returns no results.

**Sources:**

- [Dynamsoft benchmark: ZXing vs ZBar vs Dynamsoft](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
- [Jonas Neubert: Best Python packages for reading barcodes](https://blog.jonasneubert.com/2022/09/30/the-best-python-packages-for-reading-barcodes/)
- [PyPI: pyzbar](https://pypi.org/project/pyzbar/)
- [GitHub: zxing-cpp](https://github.com/zxing-cpp/zxing-cpp)
