# PRD: Barcode Validator

## Problem

NCL validates label proofs manually with phone barcode scanner app. Slow, error-prone. Misread/missed barcode → wrong labels printed → Amazon FBA rejections, wasted materials, delayed shipments.

## Goal

Python tool + AI agent skill. Automates barcode validation on label proofs. Input: PDF/image + optional expected values. Output: extracted barcodes, classification, pass/fail.

**Core decoding and validation engine is fully offline. The optional lookup extension makes network calls to free public APIs (Open Food Facts, UPCitemdb) to retrieve product information. Use `--no-lookup` to disable.**

## Users

- NCL label ops team (primary)
- AI agents via skill (secondary)

## Core Workflow

```text
Input: PDF/image (label proof) + expected barcode value(s)

Processing:
  1. Render PDF pages → images (or accept image direct)
  2. Preprocess for barcode detection
  3. Decode all barcodes
  4. Classify type (FNSKU, UPC, EAN, ISBN, etc.)
  5. Validate: format regex, check digit (MOD 10), compare expected
  6. Generate report

Output: barcodes found (value, type, symbology, page) + validation per barcode + overall verdict
```

## Barcode Types

| Type | Format | Validation |
| ---- | ------ | ---------- |
| FNSKU | `X00` + 7 alphanum (Code 128) | Regex, value match |
| UPC-A | 12 digits | MOD 10 check digit |
| UPC-E | 8 digits | Check digit |
| EAN-13 | 13 digits | MOD 10 check digit |
| EAN-8 | 8 digits | Check digit |
| ISBN-13 | 13 digits, 978/979 prefix | Check digit |
| ASIN | 10 alphanum, B0 prefix | Regex |
| Code 128 | Variable alphanum | Symbology check |
| Code 39 | Variable alphanum | Symbology check |

## Functional Requirements

### FR-1: File Input

- PDF (single/multi-page), AI (PDF-compatible), PSD (flattened composite via Pillow)
- Images: PNG, JPG, TIFF, BMP
- Render PDF/AI at 300 DPI / 2x scale

### FR-2: Detection & Decoding

- Decode all barcodes on page/image
- 1D: UPC-A/E, EAN-13/8, Code 128, Code 39
- 2D: QR, Data Matrix (stretch goal)
- Optimized for clean, high-res label proofs

### FR-3: Classification

- Auto-detect type from decoded text via pattern matching
- FNSKU (X00 prefix) vs generic Code 128
- ISBN-13 (978/979 prefix) vs generic EAN-13

### FR-4: Validation

- Check digit (MOD 10) for UPC/EAN
- Format regex for all types
- Optional comparison against expected values

### FR-4.1: Modes

- **Decode-only** (no expected): decode, classify, validate check digits, report
- **Comparison** (expected provided): decode + validate + compare, pass/fail

### FR-5: Report

- Per barcode: value, type, symbology, page
- Per barcode: pass/fail with reason
- Overall label verdict

### FR-6: CLI

- File path, expected barcodes, options as args
- JSON output + human-readable summary

### FR-7: Python API

- `validate_label()` function for integration
- Clean input/output contracts for skill use

## Non-Functional Requirements

- **Self-contained:** Core pipeline is offline. Optional lookup uses free public APIs (no auth). Minimal system deps.
- **Performance:** < 1 second per proof. Batch support.
- **Accuracy:** 95%+ detection on clean proofs. Zero false positive on check digits.
- **Portability:** macOS, Linux, Windows. Python 3.13+.

## Out of Scope (v1)

- Barcode generation
- OCR of non-barcode text
- Web UI / GUI
- Amazon scraping
- Camera/scanner input
- Layout/design validation

## Output Schema

JSON per file. Contract for AI agent integration.

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
      "matches_expected": true,
      "lookup": {
        "found": true,
        "product_name": "Example Product",
        "brand": "Example Brand",
        "source": "open_food_facts"
      }
    }
  ],
  "expected_not_found": [],
  "summary": "1 barcode found. All validations passed."
}
```

### Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `file` | string | Input file path |
| `passed` | bool | Overall verdict. Decode-only: true if format/checkdigit valid. Comparison: true if all expected found + matched. |
| `mode` | string | `"decode"` or `"comparison"` |
| `barcodes` | array | All detected barcodes |
| `barcodes[].value` | string | Decoded text |
| `barcodes[].type` | string | `FNSKU`, `UPC_A`, `UPC_E`, `EAN_13`, `EAN_8`, `ISBN_13`, `ASIN`, `CODE128`, `CODE39`, `UNKNOWN` |
| `barcodes[].symbology` | string | Raw symbology from decoder |
| `barcodes[].page` | int | 1-indexed. Always 1 for images. |
| `barcodes[].valid_format` | bool | Matches regex for its type |
| `barcodes[].valid_checkdigit` | bool/null | Check digit result. `null` for types without (FNSKU, ASIN). |
| `barcodes[].matches_expected` | bool/null | Matches expected value. `null` in decode-only. |
| `barcodes[].lookup` | object/null | Product lookup result. `null` when lookup disabled (`--no-lookup`). Object has `found`, `product_name`, `brand`, `source`. Does not affect `passed`. |
| `expected_not_found` | string[] | Expected values not found. Empty in decode-only. |
| `summary` | string | One-line human summary |

## Tech Stack

| Component | Library | Why |
| --------- | ------- | --- |
| PDF/AI render | PyMuPDF (`fitz`) | Self-contained, fastest, no system deps. Handles `.ai` as PDF. |
| Preprocessing | OpenCV (`cv2`) | Grayscale, blur, threshold |
| Decode (primary) | zxing-cpp | Active (v3.0.0), zero system deps, broad format support |
| Decode (fallback) | pyzbar | Better multi-barcode, needs zbar system lib |
| Image/PSD | Pillow | Standard. Reads `.psd` flattened composite. |
| Validation | Custom Python | Check digits, regex, comparison |

## Success Criteria

1. Correctly decodes FNSKU from NCL label proofs
2. Correctly validates UPC/EAN check digits
3. Matches decoded barcode against expected, reports pass/fail
4. Under 1 second per label
5. No internet required
6. Works as CLI + Python API
