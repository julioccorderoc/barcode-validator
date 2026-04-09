# barcode-validator

[![CI](https://github.com/julioccorderoc/barcode-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/julioccorderoc/barcode-validator/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/julioccorderoc/barcode-validator)](https://github.com/julioccorderoc/barcode-validator/blob/main/LICENSE)
[![Skills.sh](https://img.shields.io/badge/skills.sh-compatible-brightgreen)](https://skills.sh)

**An AI agent skill that validates barcodes on label proofs.** Give it a PDF, AI, PSD, or image file — it decodes every barcode, classifies them (FNSKU, UPC-A, EAN-13, etc.), validates format and check digits, looks up product info, and returns structured JSON with a pass/fail verdict.

Built for AI agents. Works as a CLI too.

## Use as an AI Agent Skill

barcode-validator ships a [SKILL.md](SKILL.md) for AI agent discovery via [skills.sh](https://skills.sh).

### Install the skill

```bash
npx skills add julioccorderoc/barcode-validator
```

### Agent invocation

The `scripts/validate.sh` wrapper adds `--json` automatically:

```bash
./scripts/validate.sh label-proof.pdf
./scripts/validate.sh label-proof.pdf --expected X001ABC1234
```

Agents get structured JSON on stdout — parse the output, check exit codes, done. See [SKILL.md](SKILL.md) for the full agent contract: triggers, examples, output schema, and error handling.

## Use as a CLI Utility

### Install from source

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/julioccorderoc/barcode-validator.git
cd barcode-validator
uv sync
```

### Install as a dependency

```bash
uv add barcode-validator
```

### Commands

**Decode-only** — extract and validate all barcodes:

```bash
barcode-validator label-proof.pdf --json
```

**Comparison mode** — check against expected values:

```bash
barcode-validator label-proof.pdf --expected X001ABC1234 --expected 0850031591271 --json
```

**Save results to file** (`--output` implies `--json`):

```bash
barcode-validator label-proof.pdf --output results.json
```

**Human-readable output** — omit `--json` for a summary on stderr:

```bash
barcode-validator label-proof.pdf
```

**Multiple files:**

```bash
barcode-validator proof1.pdf proof2.pdf --json
```

**Offline mode** — disable product lookup:

```bash
barcode-validator label-proof.pdf --json --no-lookup
```

## Product Lookup

By default, barcode-validator queries free public APIs (Open Food Facts, UPCitemdb) to enrich results with product names and descriptions. Lookup is informational only — it never affects the pass/fail verdict. Use `--no-lookup` to disable all network calls.

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
      "matches_expected": null,
      "lookup": null
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
| `barcodes[].lookup` | object/null | Product lookup result (null when `--no-lookup`) |

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

## Python API

```python
from barcode_validator import validate_label

result = validate_label("label-proof.pdf", expected=["X001ABC1234"])
print(result.passed)       # True/False
print(result.to_json())    # Full JSON output
```

## Development

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/julioccorderoc/barcode-validator.git
cd barcode-validator
uv sync
uv run pytest
```

### Project structure

```text
barcode-validator/
├── src/barcode_validator/   # Source code
├── tests/                   # pytest test suite
├── scripts/                 # Shell wrappers (agent invocation)
├── spec/                    # Architecture Decision Records
├── docs/                    # PRD, roadmap, research
├── SKILL.md                 # AI agent skill definition
└── pyproject.toml           # Package configuration
```
