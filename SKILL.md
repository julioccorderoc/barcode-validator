---
name: barcode-validator
description: Validate barcodes on label proofs (PDF, AI, PSD, PNG, JPG, TIFF, BMP). Extracts barcodes, classifies type (FNSKU, UPC-A, EAN-13, etc.), validates format and check digits, optionally compares against expected values. Returns structured JSON. Fully offline.
---

# barcode-validator

Validate barcodes on label (from designer and proofs from printers). Decodes barcodes from files, classifies them by type, validates format and check digits, and optionally compares against expected values

## When to Use

- User asks to validate, scan, or check barcodes on a label proof
- User asks to verify FNSKU, UPC, or EAN on a PDF/image
- User provides a label proof file and expected barcode values to compare
- User wants to check if a barcode's check digit is valid

## Prerequisites

- Python 3.13+
- Install: `uv add barcode-validator` (if published) or `uv pip install -e .` (from source)
- Verify: `barcode-validator --help`

## Usage

Always use `--json` for structured output, or `--output <path>` to save results to a file. Alternatively, use `./scripts/validate.sh` which adds `--json` automatically.

### Decode-only (no expected values)

```bash
barcode-validator <file> --json
```

### Comparison (with expected values)

```bash
barcode-validator <file> --expected <value1> --expected <value2> --json
```

### Save results to file

```bash
barcode-validator <file> --output results.json
```

`--output` implies `--json`. Writes a JSON array of results to the specified path.

## Examples

### Decode-only

```bash
barcode-validator "label-proof.pdf" --json
```

```json
{
  "file": "label-proof.pdf",
  "passed": true,
  "mode": "decode",
  "barcodes": [
    {
      "value": "X001ABC1234",
      "type": "FNSKU",
      "symbology": "Code128",
      "page": 1,
      "valid_format": true,
      "valid_checkdigit": null,
      "matches_expected": null
    }
  ],
  "expected_not_found": [],
  "summary": "1 barcode(s) found. All validations passed."
}
```

### Comparison mode

```bash
barcode-validator "label-proof.pdf" --expected X001ABC1234 --json
```

```json
{
  "file": "label-proof.pdf",
  "passed": true,
  "mode": "comparison",
  "barcodes": [
    {
      "value": "X001ABC1234",
      "type": "FNSKU",
      "symbology": "Code128",
      "page": 1,
      "valid_format": true,
      "valid_checkdigit": null,
      "matches_expected": true
    }
  ],
  "expected_not_found": [],
  "summary": "1 barcode(s) found. All validations passed."
}
```

## Output Schema

| Field                          | Type              | Description                                                                  |
|--------------------------------|-------------------|------------------------------------------------------------------------------|
| `file`                         | string            | Input file path                                                              |
| `passed`                       | boolean           | Overall verdict                                                              |
| `mode`                         | string            | `"decode"` or `"comparison"`                                                 |
| `barcodes`                     | array             | Extracted barcode results                                                    |
| `barcodes[].value`             | string            | Decoded barcode value                                                        |
| `barcodes[].type`              | string            | See Barcode Types Recognized section                                         |
| `barcodes[].symbology`         | string            | Raw symbology from decoder (e.g., Code128, EAN13)                            |
| `barcodes[].page`              | integer           | Page number (1-indexed, 0 for single-page images)                            |
| `barcodes[].valid_format`      | boolean           | Format matches expected pattern for classified type                          |
| `barcodes[].valid_checkdigit`  | boolean or null   | Check digit valid (null if type has no check digit)                          |
| `barcodes[].matches_expected`  | boolean or null   | Matches an expected value (null in decode-only mode)                         |
| `expected_not_found`           | array of strings  | Expected values not found in any barcode (empty in decode mode)              |
| `summary`                      | string            | Human-readable one-liner                                                     |

### Passed Logic

- **Decode mode:** true if all barcodes have valid format AND no failed check digits
- **Comparison mode:** true if all expected values found AND all matches confirmed
- **No barcodes found (decode):** `passed: false` (no barcodes to validate)
- **No barcodes found (comparison):** `passed: false` (expected values not found)

## Exit Codes

| Code | Meaning                                                         |
|------|-----------------------------------------------------------------|
| 0    | Validation passed                                               |
| 1    | Validation failed (bad check digit, missing expected, format)   |
| 2    | Error (unsupported file, file not found, processing failure)    |

## Error Handling

| Scenario                            | Exit Code | Output                                                    | Agent Action                       |
|-------------------------------------|-----------|-----------------------------------------------------------|------------------------------------|
| Unsupported file format (e.g. .eps) | 2         | stderr: `Error: file.eps: Unsupported file format: .eps`  | Report unsupported format to user  |
| File not found                      | 2         | stderr: `Error: missing.pdf: File not found: missing.pdf` | Check file path                    |
| No barcodes found (decode mode)     | 1         | JSON with empty `barcodes` array, `passed: false`         | Report no barcodes detected        |
| No barcodes found (comparison)      | 1         | JSON with `passed: false`, `expected_not_found` populated | Report expected barcodes not found |
| Processing failure                  | 2         | stderr error message                                      | Report error to user               |

**Always check exit code first.** Parse JSON only on exit 0 or 1. On exit 2, read stderr for error details.

## Supported File Formats

PDF, AI (Adobe Illustrator, PDF-compatible), PSD, PNG, JPG/JPEG, TIFF, BMP.

EPS is **not supported**.

## Barcode Types Recognized

| Type    | Pattern                            | Validation         |
|---------|------------------------------------|--------------------|
| FNSKU   | X00 + 7 alphanumeric (Code 128)    | Regex format       |
| UPC_A   | 12 digits                          | MOD-10 check digit |
| UPC_E   | 8 digits                           | Check digit        |
| EAN_13  | 13 digits                          | MOD-10 check digit |
| EAN_8   | 8 digits                           | Check digit        |
| ISBN_13 | 13 digits, 978/979 prefix          | Check digit        |
| ASIN    | 10 alphanumeric, B0 prefix         | Regex format       |
| CODE128 | Variable alphanumeric              | Symbology check    |
| CODE39  | Variable alphanumeric              | Symbology check    |
| UNKNOWN | No pattern matched                 | None               |
