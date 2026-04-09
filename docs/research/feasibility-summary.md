# Feasibility Summary: Automated Barcode Validation Skill

> 2026-04-09

## The Problem

Label proofs for Amazon FBA products are currently validated manually with a barcode scanner before approving printing. This is slow and error-prone.

## Is It Feasible?

**Yes, fully feasible with open-source Python libraries. No external APIs required.**

## Recommended Stack

| Step | Library | Self-Contained? |
|------|---------|-----------------|
| PDF → Image | PyMuPDF (`fitz`) | Yes (bundled) |
| Image preprocessing | OpenCV (`cv2`) | Yes (pip) |
| Barcode decoding | pyzbar | Mostly (needs zbar system lib on macOS/Linux) |
| Barcode decoding (alt) | zxing-cpp | Yes (pure wheels) |
| Validation logic | Custom Python | Yes |

### Only System Dependency

`pyzbar` requires the zbar C library:

- macOS: `brew install zbar`
- Linux: `apt install libzbar0`
- Windows: bundled automatically

If even this is unacceptable, `zxing-cpp` is a pure-pip alternative (trade-off: worse multi-barcode detection).

## What the Skill Would Do

```text
Input: PDF/image of label proof + expected barcode value(s)
    ↓
1. Render PDF to image (PyMuPDF, ~3ms)
2. Preprocess image (OpenCV grayscale/blur/threshold, ~5ms)
3. Decode all barcodes on the label (pyzbar, ~50-100ms)
4. For each barcode found:
   a. Classify type (UPC/EAN/FNSKU/ASIN/ISBN by pattern matching)
   b. Validate check digit (MOD 10 for UPC/EAN)
   c. Validate format (regex for FNSKU X00 prefix, etc.)
   d. Compare against expected value
5. Report: pass/fail with details
    ↓
Output: Validation result (which barcodes found, types, values, pass/fail)
```

**Total processing time: ~60-110ms per label page.**

## Supported Barcode Types

| Type | Detection | Validation |
|------|-----------|------------|
| UPC-A/E | pyzbar ✓ | Check digit (MOD 10) + format regex |
| EAN-13/8 | pyzbar ✓ | Check digit (MOD 10) + format regex |
| FNSKU | pyzbar ✓ (Code 128) | X00 prefix + format regex |
| ASIN | Detected as Code 128 text | B0 prefix + format regex |
| ISBN-13 | pyzbar ✓ (EAN-13) | 978/979 prefix + check digit |
| Code 128 | pyzbar ✓ | Symbology-level validation |
| Code 39 | pyzbar ✓ | Symbology-level validation |

## Key Capabilities

- **Multi-barcode detection:** pyzbar handles multiple barcodes per image (85% success)
- **Rotation tolerance:** Moderate rotation handled by pyzbar; OpenCV preprocessing helps more
- **PDF and image input:** Supports both via PyMuPDF rendering
- **Auto-classification:** Automatically identifies barcode type from decoded text pattern
- **Check digit validation:** Mathematical verification for UPC/EAN without any database lookup

## Risks & Limitations

1. **Accuracy:** pyzbar achieves ~71% on diverse real-world images, but label proofs are clean/high-quality — expect much higher accuracy on controlled inputs
2. **System dependency:** zbar needs to be installed on the machine (one-time setup)
3. **No product data lookup:** Without an API, we can validate format/checksum but can't verify "this UPC belongs to Product X" (would need a database)
4. **Amazon scraping:** Not recommended for a self-contained skill due to anti-bot measures

## Conclusion

This is a straightforward project. The libraries are mature, the pipeline is well-established, and label proofs (clean, high-resolution PDFs) are the **easiest** input type for barcode scanners — much easier than photographed real-world labels. Expected accuracy on clean label proofs should be 95%+.
