# EPIC-005: SKILL.md Design Spec

## Context

barcode-validator is a CLI tool that validates barcodes on label proofs for Amazon FBA. EPICs 001-004 are complete: the tool decodes barcodes from PDF/AI/PSD/image files, classifies them, validates format and check digits, compares against expected values, and outputs structured JSON. EPIC-005 makes this tool discoverable and invocable by AI agents through a `SKILL.md` file at the project root.

## Decision

Single `SKILL.md` at project root. Self-contained — an agent reading only this file can invoke the CLI correctly and parse results. CLI-only interface (not the Python API). No code changes.

## SKILL.md Structure

### Frontmatter

```yaml
---
name: barcode-validator
description: Validate barcodes on label proofs (PDF, AI, PSD, PNG, JPG, TIFF, BMP). Extracts barcodes, classifies type (FNSKU, UPC-A, EAN-13, etc.), validates format and check digits, optionally compares against expected values. Returns structured JSON. Fully offline.
---
```

### Body Sections (in order)

#### 1. When to Use
Trigger conditions for agent invocation:
- User asks to validate, scan, or check barcodes on a label proof
- User asks to verify FNSKU, UPC, or EAN on a PDF/image
- User provides a label proof file and expected barcode values to compare
- User wants to check if a barcode's check digit is valid

#### 2. Prerequisites
- Python 3.13+
- Install: `uv pip install barcode-validator`
- Verify: `barcode-validator --help`

#### 3. Usage
Two modes:

**Decode-only** (no expected values):
```
barcode-validator <file> --json
```

**Comparison** (with expected values):
```
barcode-validator <file> --expected <value1> --expected <value2> --json
```

Always use `--json` for structured output.

#### 4. Examples

**Decode-only:**
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

**Comparison mode:**
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

#### 5. Output Schema

| Field | Type | Description |
|-------|------|-------------|
| `file` | string | Input file path |
| `passed` | boolean | Overall verdict |
| `mode` | `"decode"` \| `"comparison"` | Decode-only or comparison mode |
| `barcodes` | array | Extracted barcode results |
| `barcodes[].value` | string | Decoded barcode value |
| `barcodes[].type` | string | Classification: FNSKU, UPC_A, EAN_13, EAN_8, UPC_E, ISBN_13, ASIN, CODE128, CODE39, UNKNOWN |
| `barcodes[].symbology` | string | Raw symbology from decoder (e.g., Code128, EAN13) |
| `barcodes[].page` | integer | Page number (1-indexed, 0 for single-page images) |
| `barcodes[].valid_format` | boolean | Format matches expected pattern for classified type |
| `barcodes[].valid_checkdigit` | boolean \| null | Check digit valid (null if type has no check digit) |
| `barcodes[].matches_expected` | boolean \| null | Matches an expected value (null in decode-only mode) |
| `expected_not_found` | array of strings | Expected values not found in any barcode (empty in decode mode) |
| `summary` | string | Human-readable one-liner |

**`passed` logic:**
- Decode mode: true if all barcodes have valid format AND no failed check digits
- Comparison mode: true if all expected values found AND all matches confirmed
- Empty barcodes array (no barcodes found): `passed: false` in decode mode (no barcodes to validate)

#### 6. Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed |
| 1 | Validation failed (bad check digit, missing expected, format error) |
| 2 | Error (unsupported file, file not found, processing failure) |

#### 7. Error Handling

| Scenario | Exit Code | Output | Agent action |
|----------|-----------|--------|--------------|
| Unsupported file format (e.g., .eps) | 2 | stderr: `Error: file.eps: Unsupported file format: .eps` | Report unsupported format to user |
| File not found | 2 | stderr: `Error: missing.pdf: [Errno 2] No such file or directory` | Check file path |
| No barcodes found (decode mode) | 1 | JSON with empty `barcodes` array, `passed: false` | Report that no barcodes were detected |
| No barcodes found (comparison mode) | 1 | JSON with empty `barcodes` array, `passed: false`, `expected_not_found` populated | Report expected barcodes were not found |
| Processing failure | 2 | stderr error message | Report error to user |

**Agent guidance:** Always check exit code first. Parse JSON only on exit 0 or 1. On exit 2, read stderr for error details.

#### 8. Supported File Formats

PDF, AI (Adobe Illustrator, PDF-compatible), PSD, PNG, JPG/JPEG, TIFF, BMP.

EPS is **not supported**.

#### 9. Barcode Types Recognized

| Type | Pattern | Validation |
|------|---------|------------|
| FNSKU | X00 + 7 alphanumeric (Code 128) | Regex format |
| UPC-A | 12 digits | MOD-10 check digit |
| UPC-E | 8 digits | Check digit |
| EAN-13 | 13 digits | MOD-10 check digit |
| EAN-8 | 8 digits | Check digit |
| ISBN-13 | 13 digits, 978/979 prefix | Check digit |
| ASIN | 10 alphanumeric, B0 prefix | Regex format |
| CODE128 | Variable alphanumeric | Symbology check |
| CODE39 | Variable alphanumeric | Symbology check |

## Project Restructuring

Add skill-convention directories alongside the existing Python package:

```text
barcode-validator/
├── SKILL.md              # NEW — skill definition
├── scripts/              # NEW — shell wrapper for agent invocation
│   └── validate.sh       # Thin wrapper around `barcode-validator` CLI
├── CLAUDE.md             # existing
├── pyproject.toml        # existing (no changes)
├── src/                  # existing Python package (no changes)
│   └── barcode_validator/
├── tests/                # existing
├── docs/                 # existing (build-time docs, not moved)
├── spec/                 # existing
└── plans/                # existing
```

`references/` and `assets/` are not needed — no runtime reference docs or static assets required.

### scripts/validate.sh

A thin shell wrapper that agents can execute directly:

```bash
#!/usr/bin/env bash
# Wrapper for barcode-validator CLI — intended for AI agent invocation.
# Usage: ./scripts/validate.sh <file> [--expected <value>]
set -euo pipefail
exec barcode-validator "$@" --json
```

This ensures agents always get JSON output without needing to remember `--json`.

## Files to Create

| File                  | Action                             |
|-----------------------|------------------------------------|
| `SKILL.md`            | Create at project root             |
| `scripts/validate.sh` | Shell wrapper for agent invocation |

## Files to Modify

| File | Change |
|------|--------|
| `docs/roadmap.md` | Mark EPIC-005 as Complete |

## No Python Code Changes

The CLI and Python API are complete and working. `src/barcode_validator/` is untouched.

## Verification

1. `SKILL.md` exists at project root with valid YAML frontmatter
2. An agent (or human) reading only SKILL.md can:
   - Determine when to use the tool (trigger conditions)
   - Invoke it correctly for decode-only and comparison modes
   - Parse the JSON output using the schema
   - Handle errors appropriately using exit codes
3. All existing tests still pass: `uv run pytest`
4. Manual test: run the CLI examples from SKILL.md against a `test_docs/` file and verify output matches the documented schema
