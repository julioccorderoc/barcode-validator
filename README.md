# barcode-validator

[![CI](https://github.com/julioccorderoc/barcode-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/julioccorderoc/barcode-validator/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/julioccorderoc/barcode-validator)](https://github.com/julioccorderoc/barcode-validator/blob/main/LICENSE)
[![Skills.sh](https://img.shields.io/badge/skills.sh-compatible-brightgreen)](https://skills.sh)

Validate barcodes on label proofs. Decode, classify, check digits, compare expected values. Fully offline.

## What it does

Reads PDF, AI, PSD, and image files containing label proofs. Extracts barcodes using zxing-cpp, classifies them (FNSKU, UPC-A, EAN-13, etc.), validates format and check digits, and optionally compares against expected values. Returns structured JSON with a pass/fail verdict.

Built for NCL ops -- replaces manual barcode scanning with one command.

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

### From source

```bash
git clone <repo-url>
cd barcode-validator
uv sync
```

### As a dependency

```bash
uv add barcode-validator
```

## Usage

### Decode-only

```bash
barcode-validator label-proof.pdf --json
```

### Comparison mode

```bash
barcode-validator label-proof.pdf --expected X001ABC1234 --expected 0850031591271 --json
```

### Save results to file

```bash
barcode-validator label-proof.pdf --output results.json
```

`--output` implies `--json`. Writes a JSON array of all results to the specified path.

### Multiple files

```bash
barcode-validator proof1.pdf proof2.pdf --json
```

### Human-readable output

```bash
barcode-validator label-proof.pdf
```

Omit `--json` for a human-readable summary on stderr.

## Output Schema

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

| Field | Type | Description |
| ----- | ---- | ----------- |
| `passed` | boolean | Overall verdict |
| `mode` | string | `"decode"` or `"comparison"` |
| `barcodes[].type` | string | FNSKU, UPC_A, EAN_13, EAN_8, UPC_E, ISBN_13, ASIN, CODE128, CODE39, UNKNOWN |
| `barcodes[].valid_format` | boolean | Format matches expected pattern |
| `barcodes[].valid_checkdigit` | boolean/null | Check digit valid (null if type has none) |
| `barcodes[].matches_expected` | boolean/null | Matches expected value (null in decode mode) |

See [SKILL.md](SKILL.md) for the full schema and AI agent integration details.

## Supported File Formats

PDF, AI (Adobe Illustrator), PSD, PNG, JPG/JPEG, TIFF, BMP.

EPS is **not** supported.

## Barcode Types

| Type | Pattern | Validation |
| ---- | ------- | ---------- |
| FNSKU | X00 + 7 alphanumeric | Regex format |
| UPC-A | 12 digits | MOD-10 check digit |
| UPC-E | 8 digits | Check digit |
| EAN-13 | 13 digits | MOD-10 check digit |
| EAN-8 | 8 digits | Check digit |
| ISBN-13 | 13 digits, 978/979 prefix | Check digit |
| ASIN | 10 alphanumeric, B0 prefix | Regex format |
| CODE128 | Variable alphanumeric | Symbology check |
| CODE39 | Variable alphanumeric | Symbology check |

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0 | Validation passed |
| 1 | Validation failed (bad check digit, missing expected, format) |
| 2 | Error (unsupported file, file not found, processing failure) |

## AI Agent Integration

This tool ships a [SKILL.md](SKILL.md) for AI agent discovery via [skills.sh](https://skills.sh).

```bash
npx skills add <owner>/barcode-validator
```

The `scripts/validate.sh` wrapper adds `--json` automatically for agent invocation:

```bash
./scripts/validate.sh label-proof.pdf --expected X001ABC1234
```

## Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
git clone <repo-url>
cd barcode-validator
uv sync
```

### Run tests

```bash
uv run pytest
```

### Project structure

```text
barcode-validator/
├── src/barcode_validator/   # Source code
├── tests/                   # pytest test suite
├── scripts/                 # Shell wrappers
├── spec/                    # Architecture Decision Records
├── docs/                    # PRD, roadmap, research
├── SKILL.md                 # AI agent skill definition
└── pyproject.toml           # Package configuration
```
