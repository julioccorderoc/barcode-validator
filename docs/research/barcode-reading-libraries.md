# Barcode Reading Libraries for Python

> Research 2026-04-09. Self-contained, no external APIs.

## Summary

| Library | License | Types | Multi-Barcode | System Deps | Active | Accuracy |
| ------- | ------- | ----- | ------------- | ----------- | ------ | -------- |
| pyzbar | MIT+LGPL | EAN/UPC/Code128/39/QR | 85% | zbar C lib | Inactive | 71.2% |
| zxing-cpp | Apache 2.0 | Extensive 1D/2D | 23.8% | None | Active | 65.9% |
| pyzxing | Open | Extensive 1D/2D | One only | Java/JVM | Low | N/A |
| OpenCV | BSD | EAN only | N/A | None | Active | N/A |
| Dynamsoft | Commercial | Extensive | Good | None | Active | 90.6% |
| pylibdmtx | Open | Data Matrix only | Good | libdmtx | Low | N/A |

---

## pyzbar

Wrapper around ZBar C library. EAN-13/8, UPC-A/E, Code 128/93/39, Codabar, I2of5, QR.

- **License:** MIT (wrapper) + LGPL v2.1 (zbar)
- **System deps:** zbar lib (macOS: `brew install zbar`, Linux: `apt install libzbar0`, Windows: bundled)
- **Accuracy:** 71.2% real-world, 85% multi-barcode
- **Status:** Inactive (12+ months no releases), 112K weekly downloads
- **Verdict:** Best accuracy + multi-barcode. Stable C lib despite abandoned wrapper.

## python-barcode

**GENERATION ONLY.** Does not decode. Not suitable.

## zxing-cpp

C++ ZXing port with Python bindings. 1D: Codabar, Code39/93/128, EAN8/13, ITF, UPC-A/E, DataBar. 2D: QR, Micro QR, Aztec, Data Matrix, PDF417, MaxiCode.

- **License:** Apache 2.0
- **System deps:** None (pure C++ wheels)
- **Performance:** 40.2 ms avg, 65.9% accuracy
- **v3.0.0 (Feb 2026):** `read_barcodes()` multi-barcode API. Python 3.10-3.14.
- **Verdict:** Best self-contained choice. Zero deps, active, broad formats. Multi-barcode trails pyzbar on messy images but likely fine for clean proofs.

## pyzxing

Java ZXing wrapper via subprocess. Requires JVM. **Not recommended** — zxing-cpp better in every way.

## OpenCV barcode

EAN-8/13, UPC-A/E only. No Code128/39. Requires `opencv-contrib-python`. **Insufficient coverage.** Best as preprocessing before pyzbar/zxing.

## Dynamsoft

Commercial. Best accuracy (90.6%) but requires paid license.

## pylibdmtx

Data Matrix only. Requires libdmtx. Niche.

---

## Recommendation

**Primary:** zxing-cpp — zero deps, active, broad formats.
**Preprocessing:** OpenCV — grayscale, blur, threshold.
**Fallback:** pyzbar — better multi-barcode if zxing-cpp misses.

**Sources:**

- [Dynamsoft benchmark](https://www.dynamsoft.com/codepool/python-zxing-zbar-barcode.html)
- [Jonas Neubert: Best Python barcode packages](https://blog.jonasneubert.com/2022/09/30/the-best-python-packages-for-reading-barcodes/)
- [PyPI: pyzbar](https://pypi.org/project/pyzbar/)
- [GitHub: zxing-cpp](https://github.com/zxing-cpp/zxing-cpp)
