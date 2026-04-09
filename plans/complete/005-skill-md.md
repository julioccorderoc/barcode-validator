# EPIC-005: SKILL.md Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make barcode-validator discoverable and invocable by AI agents via a SKILL.md file and shell wrapper script.

**Architecture:** Single SKILL.md at project root with YAML frontmatter and self-contained documentation. A thin shell wrapper in scripts/validate.sh ensures agents always get JSON output. No Python code changes.

**Tech Stack:** Markdown (YAML frontmatter), Bash

---

### Task 1: Create scripts/validate.sh

**Files:**
- Create: `scripts/validate.sh`

- [ ] **Step 1: Create the scripts directory and wrapper**

```bash
mkdir -p scripts
```

Write `scripts/validate.sh`:

```bash
#!/usr/bin/env bash
# Wrapper for barcode-validator CLI — intended for AI agent invocation.
# Usage: ./scripts/validate.sh <file> [--expected <value>]
set -euo pipefail
exec barcode-validator "$@" --json
```

- [ ] **Step 2: Make it executable**

```bash
chmod +x scripts/validate.sh
```

- [ ] **Step 3: Verify it works**

Run against a test file:

```bash
./scripts/validate.sh "test_docs/(proof)(BL6)(540841).pdf"
```

Expected: JSON output to stdout with `"passed"`, `"mode": "decode"`, `"barcodes"` array containing decoded values. Exit code 0.

Verify exit code:

```bash
echo $?
```

Expected: `0`

- [ ] **Step 4: Commit**

```bash
git add scripts/validate.sh
git commit -m "feat(epic-005): add scripts/validate.sh agent wrapper"
```

---

### Task 2: Create SKILL.md

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: Write SKILL.md at project root**

```markdown
---
name: barcode-validator
description: Validate barcodes on label proofs (PDF, AI, PSD, PNG, JPG, TIFF, BMP). Extracts barcodes, classifies type (FNSKU, UPC-A, EAN-13, etc.), validates format and check digits, optionally compares against expected values. Returns structured JSON. Fully offline.
---

# barcode-validator

Validate barcodes on label proofs for Amazon FBA. Decodes barcodes from files, classifies them by type, validates format and check digits, and optionally compares against expected values.

## When to Use

- User asks to validate, scan, or check barcodes on a label proof
- User asks to verify FNSKU, UPC, or EAN on a PDF/image
- User provides a label proof file and expected barcode values to compare
- User wants to check if a barcode's check digit is valid

## Prerequisites

- Python 3.13+
- Install: `uv pip install barcode-validator`
- Verify: `barcode-validator --help`

## Usage

Always use `--json` for structured output. Alternatively, use `./scripts/validate.sh` which adds `--json` automatically.

### Decode-only (no expected values)

```bash
barcode-validator <file> --json
```

### Comparison (with expected values)

```bash
barcode-validator <file> --expected <value1> --expected <value2> --json
```

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
| `barcodes[].type`              | string            | FNSKU, UPC_A, EAN_13, EAN_8, UPC_E, ISBN_13, ASIN, CODE128, CODE39, UNKNOWN |
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
- **No barcodes found (decode):** `passed: true` (vacuously valid)
- **No barcodes found (comparison):** `passed: false` (expected values not found)

## Exit Codes

| Code | Meaning                                                         |
|------|-----------------------------------------------------------------|
| 0    | Validation passed                                               |
| 1    | Validation failed (bad check digit, missing expected, format)   |
| 2    | Error (unsupported file, file not found, processing failure)    |

## Error Handling

| Scenario                          | Exit Code | Output                                                      | Agent Action                          |
|-----------------------------------|-----------|-------------------------------------------------------------|---------------------------------------|
| Unsupported file format (e.g. .eps) | 2       | stderr: `Error: file.eps: Unsupported file format: .eps`    | Report unsupported format to user     |
| File not found                    | 2         | stderr: `Error: missing.pdf: No such file or directory`     | Check file path                       |
| No barcodes found (decode mode)   | 0         | JSON with empty `barcodes` array, `passed: true`            | Report no barcodes detected           |
| No barcodes found (comparison)    | 1         | JSON with `passed: false`, `expected_not_found` populated   | Report expected barcodes not found    |
| Processing failure                | 2         | stderr error message                                        | Report error to user                  |

**Always check exit code first.** Parse JSON only on exit 0 or 1. On exit 2, read stderr for error details.

## Supported File Formats

PDF, AI (Adobe Illustrator, PDF-compatible), PSD, PNG, JPG/JPEG, TIFF, BMP.

EPS is **not supported**.

## Barcode Types Recognized

| Type    | Pattern                            | Validation         |
|---------|------------------------------------|--------------------|
| FNSKU   | X00 + 7 alphanumeric (Code 128)   | Regex format       |
| UPC-A   | 12 digits                          | MOD-10 check digit |
| UPC-E   | 8 digits                           | Check digit        |
| EAN-13  | 13 digits                          | MOD-10 check digit |
| EAN-8   | 8 digits                           | Check digit        |
| ISBN-13 | 13 digits, 978/979 prefix          | Check digit        |
| ASIN    | 10 alphanumeric, B0 prefix         | Regex format       |
| CODE128 | Variable alphanumeric              | Symbology check    |
| CODE39  | Variable alphanumeric              | Symbology check    |
```

- [ ] **Step 2: Verify frontmatter is valid YAML**

```bash
head -4 SKILL.md
```

Expected:
```
---
name: barcode-validator
description: Validate barcodes on label proofs...
---
```

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "feat(epic-005): add SKILL.md agent skill definition"
```

---

### Task 3: Verify and Close Epic

**Files:**
- Modify: `docs/roadmap.md:66-77`

- [ ] **Step 1: Run existing tests to confirm nothing broke**

```bash
uv run pytest
```

Expected: All tests pass (216 passed). No regressions.

- [ ] **Step 2: Run CLI via the wrapper against a real test file**

```bash
./scripts/validate.sh "test_docs/(proof)(BL6)(540841).pdf"
```

Expected: JSON output with decoded barcodes, `"passed": true`, `"mode": "decode"`. Verify the output structure matches the schema documented in SKILL.md.

- [ ] **Step 3: Run CLI in comparison mode**

```bash
./scripts/validate.sh "test_docs/(proof)(BL6)(540841).pdf" --expected X001234567
```

Expected: JSON output with `"mode": "comparison"`. If `X001234567` is not on the label, `"passed": false` and `"expected_not_found": ["X001234567"]`.

- [ ] **Step 4: Test error path**

```bash
./scripts/validate.sh "nonexistent.pdf" 2>&1; echo "exit: $?"
```

Expected: stderr error message, exit code 2.

- [ ] **Step 5: Update roadmap — mark EPIC-005 as Complete**

In `docs/roadmap.md`, change EPIC-005's status:

```markdown
- Status: Complete
```

- [ ] **Step 6: Final commit**

```bash
git add docs/roadmap.md
git commit -m "chore(epic-005): mark epic complete"
```
