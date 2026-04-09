# PRD: Barcode Validator

## Problem

NCL validates label proofs manually with a physical barcode scanner (an app in the phone) before approving them for printing. This is repetitive, slow, and error-prone. A misread or missed barcode can result in incorrect labels being printed en masse, leading to Amazon FBA rejections, wasted materials, and delayed shipments.

## Goal

Build a self-contained Python tool (and AI agent skill) that automates barcode validation on label proofs. Given a PDF or image of a label proof and the expected barcode value(s), the tool extracts all barcodes, classifies their type, validates their integrity, and reports pass/fail.

**No external APIs required.** The tool must run fully offline.

## Users

- NCL label operations team (primary)
- AI agents via skill integration (secondary)

## Core Workflow

```text
Input:
  - PDF or image file (label proof)
  - Expected barcode value(s) and/or type(s)

Processing:
  1. Render PDF pages to images (or accept image directly)
  2. Preprocess image for optimal barcode detection
  3. Decode all barcodes found on the label
  4. Classify each barcode type (FNSKU, UPC, EAN, ISBN, etc.)
  5. Validate each barcode:
     a. Format validation (regex pattern match)
     b. Check digit validation (MOD 10 for UPC/EAN)
     c. Value comparison against expected barcode(s)
  6. Generate validation report

Output:
  - List of barcodes found (value, type, symbology, position)
  - Validation result per barcode (pass/fail with reason)
  - Overall label verdict (pass/fail)
```

## Supported Barcode Types

| Type | Format | Validation |
|------|--------|------------|
| FNSKU | `X00` + 7 alphanumeric (Code 128) | Format regex, value match |
| UPC-A | 12 numeric digits | Check digit (MOD 10), format |
| UPC-E | 8 numeric digits | Check digit, format |
| EAN-13 | 13 numeric digits | Check digit (MOD 10), format |
| EAN-8 | 8 numeric digits | Check digit, format |
| ISBN-13 | 13 digits, 978/979 prefix | Check digit, format |
| ASIN | 10 alphanumeric, B0 prefix | Format regex |
| Code 128 | Variable alphanumeric | Symbology check |
| Code 39 | Variable alphanumeric | Symbology check |

## Functional Requirements

### FR-1: File Input

- Accept PDF files (single or multi-page)
- Accept Adobe Illustrator files (`.ai`) — treated as PDF (AI files saved with "Create PDF Compatible File" are valid PDFs)
- Accept Photoshop files (`.psd`) — read flattened composite via Pillow
- Accept image files (PNG, JPG, TIFF, BMP)
- Render PDFs/AI files to images at sufficient resolution for barcode detection (300 DPI / 2x scale)

### FR-2: Barcode Detection & Decoding

- Detect and decode all barcodes on a page/image
- Support 1D barcodes: UPC-A/E, EAN-13/8, Code 128, Code 39
- Support 2D barcodes: QR Code, Data Matrix (stretch goal)
- Handle clean, high-resolution label proofs (primary use case)

### FR-3: Barcode Classification

- Auto-detect barcode type from decoded text using pattern matching
- Distinguish FNSKU (X00 prefix) from generic Code 128
- Distinguish ISBN-13 (978/979 prefix) from generic EAN-13

### FR-4: Barcode Validation

- Check digit validation for UPC and EAN barcodes
- Format validation via regex for all supported types
- Comparison against user-provided expected value(s) (optional — tool works without expected values)

### FR-4.1: Usage Modes

- **Decode-only mode** (no expected values): decode all barcodes, classify types, validate check digits, report findings
- **Comparison mode** (expected values provided): decode + validate + compare against expected values, report pass/fail

### FR-5: Validation Report

- Report each barcode found: value, classified type, symbology, page/position
- Report validation status per barcode: pass, fail (with reason)
- Report overall label verdict

### FR-6: CLI Interface

- Command-line interface for direct use
- Accept file path, expected barcode(s), and options as arguments
- Output structured results (JSON) and human-readable summary

### FR-7: Programmatic API

- Python function/class API for integration into other tools and AI agent skills
- Clean input/output contracts for skill integration

## Non-Functional Requirements

### NFR-1: Self-Contained

- No external API calls for barcode decoding or validation
- Minimal system dependencies (prefer pure-pip packages)
- Must run fully offline

### NFR-2: Performance

- Process a single label proof in under 1 second
- Support batch processing of multiple files

### NFR-3: Accuracy

- Target 95%+ detection rate on clean label proofs (PDF/high-res images)
- Zero false positives on check digit validation (deterministic algorithm)

### NFR-4: Portability

- Run on macOS, Linux, and Windows
- Python 3.13+

## Out of Scope (v1)

- Barcode generation or creation
- OCR of non-barcode text on labels (future enhancement)
- Web UI or GUI
- Product data lookup from external databases
- Amazon page scraping
- Real-time camera/scanner input
- Label layout/design validation (margins, DPI, placement)

## Output Schema

The tool outputs a JSON object per file. This is the contract for AI agent skill integration.

```json
{
  "file": "label_proof.pdf",
  "passed": true,
  "mode": "comparison",
  "barcodes": [
    {
      "value": "X001ABC123",
      "type": "FNSKU",
      "symbology": "CODE128",
      "page": 1,
      "valid_format": true,
      "valid_checkdigit": null,
      "matches_expected": true
    }
  ],
  "expected_not_found": [],
  "summary": "1 barcode found. All validations passed."
}
```

### Field definitions

| Field | Type | Description |
| ----- | ---- | ----------- |
| `file` | string | Input file path |
| `passed` | bool | Overall verdict. In decode-only mode: true if all barcodes have valid format/check digit. In comparison mode: true only if all expected barcodes are found and match. |
| `mode` | string | `"decode"` or `"comparison"` |
| `barcodes` | array | All barcodes detected on the label |
| `barcodes[].value` | string | Decoded barcode text |
| `barcodes[].type` | string | Classified type: `FNSKU`, `UPC_A`, `UPC_E`, `EAN_13`, `EAN_8`, `ISBN_13`, `ASIN`, `CODE128`, `CODE39`, `UNKNOWN` |
| `barcodes[].symbology` | string | Raw barcode symbology from decoder (e.g., `CODE128`, `EAN13`) |
| `barcodes[].page` | int | Page number (1-indexed). Always 1 for image inputs. |
| `barcodes[].valid_format` | bool | Whether value matches expected regex pattern for its type |
| `barcodes[].valid_checkdigit` | bool or null | Check digit validation result. `null` for types without check digits (FNSKU, ASIN). |
| `barcodes[].matches_expected` | bool or null | Whether value matches an expected barcode. `null` in decode-only mode. |
| `expected_not_found` | array of string | Expected barcode values not found on the label. Empty array in decode-only mode. |
| `summary` | string | Human-readable one-line summary |

## Tech Stack

| Component | Library | Rationale |
|-----------|---------|-----------|
| PDF/AI rendering | PyMuPDF (`fitz`) | Self-contained, fastest (300+ pps), no system deps. Handles `.ai` as PDF. |
| Image preprocessing | OpenCV (`cv2`) | Grayscale, blur, threshold for detection improvement |
| Barcode decoding | zxing-cpp (primary) | Active (v3.0.0, Feb 2026), zero system deps, broad format support |
| Barcode decoding | pyzbar (optional fallback) | Better multi-barcode accuracy, requires zbar system lib |
| Image/PSD handling | Pillow | Standard Python imaging. Reads `.psd` flattened composite natively. |
| Validation | Custom Python | Check digit algorithms, regex patterns, comparison logic |

## Success Criteria

1. Tool correctly decodes FNSKU barcodes from NCL label proofs
2. Tool correctly validates UPC/EAN check digits
3. Tool matches decoded barcode against expected value and reports pass/fail
4. Processing time under 1 second per label
5. Runs without internet connection
6. Usable as both CLI tool and Python API
