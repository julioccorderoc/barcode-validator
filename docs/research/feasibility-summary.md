# Feasibility Summary: Automated Barcode Validation

> 2026-04-09

## Problem

NCL validates label proofs manually with barcode scanner. Slow, error-prone.

## Feasible?

**Yes.** Open-source Python. No external APIs. Fully offline.

## Stack

| Step | Library | Self-Contained |
| ---- | ------- | -------------- |
| PDF → Image | PyMuPDF | Yes (bundled) |
| Preprocessing | OpenCV | Yes (pip) |
| Decode | zxing-cpp | Yes (pure wheels) |
| Decode (fallback) | pyzbar | Mostly (needs zbar sys lib) |
| Validation | Custom Python | Yes |

pyzbar needs zbar: macOS `brew install zbar`, Linux `apt install libzbar0`, Windows bundled. zxing-cpp = pure-pip alternative (worse multi-barcode).

## Pipeline

```text
PDF/image + expected values
  → PyMuPDF render (~3ms)
  → OpenCV preprocess (~5ms)
  → Decode barcodes (~50-100ms)
  → Classify (UPC/EAN/FNSKU/ASIN by pattern)
  → Validate (check digit, format regex)
  → Compare expected
  → Pass/fail report
Total: ~60-110ms per page
```

## Barcode Support

| Type | Detection | Validation |
| ---- | --------- | ---------- |
| UPC-A/E | Yes | MOD 10 + regex |
| EAN-13/8 | Yes | MOD 10 + regex |
| FNSKU | Yes (Code 128) | X00 prefix + regex |
| ASIN | Code 128 text | B0 prefix + regex |
| ISBN-13 | Yes (EAN-13) | 978/979 + check digit |
| Code 128/39 | Yes | Symbology check |

## Key Capabilities

- Multi-barcode: pyzbar 85% success
- Moderate rotation tolerance
- PDF + image input
- Auto-classification by pattern
- Check digit validation without DB lookup

## Risks

1. **Accuracy:** 71% on diverse images, but clean proofs = much higher (95%+ expected)
2. **System dep:** zbar one-time install (or use zxing-cpp)
3. **No product lookup:** Validates format/checksum only, not "UPC belongs to Product X"

## Conclusion

Straightforward project. Mature libraries, established pipeline. Clean label proofs = easiest input type for barcode scanners.
