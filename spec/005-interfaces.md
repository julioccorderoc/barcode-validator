# ADR-005: CLI and Programmatic Interfaces

## Status

Accepted

## Context

The tool needs two interfaces:

1. **CLI** — primary interface, used directly and by the AI agent skill
2. **Python API** — for programmatic integration into other tools

## Decision

### Python API

A single entry-point function and a result dataclass:

```python
from barcode_validator import validate_label

# Decode-only mode (no expected values)
result = validate_label(file_path="label_proof.pdf")

# Comparison mode (with expected values)
result = validate_label(
    file_path="label_proof.pdf",
    expected_barcodes=["X001ABC123"],
)

# result.barcodes -> list of detected barcodes with type, value, validation status
# result.passed -> bool (overall verdict)
# result.summary -> str (human-readable summary)
# result.to_json() -> JSON string matching the output schema in PRD
```

### CLI (wraps Python API)

```bash
# Decode-only mode — just scan and report what's on the label
barcode-validator label_proof.pdf

# Comparison mode — validate against expected barcode(s)
barcode-validator label_proof.pdf --expected X001ABC123

# Multiple expected values
barcode-validator label_proof.pdf --expected X001ABC123 --expected 012345678905

# JSON output (default for scripting; human-readable summary also printed to stderr)
barcode-validator label_proof.pdf --json

# Supported file types: PDF, AI, PSD, PNG, JPG, TIFF, BMP
barcode-validator label_proof.ai --expected X001ABC123
barcode-validator label_design.psd --expected X001ABC123

# Batch (multiple files)
barcode-validator *.pdf --expected X001ABC123
```

### Output JSON schema

Defined in the PRD (`docs/PRD.md` > Output Schema). This is the canonical reference for the output contract.

### Why CLI as primary

- The AI agent skill invokes this as a CLI command
- CLI is the natural interface for the operations team
- Python API exists for deeper integration but CLI is the stable contract

### Why two modes

- **Decode-only** is useful for initial exploration: "what's on this label?"
- **Comparison** is the main validation workflow: "is this the right barcode?"
- Same pipeline, comparison is just an optional final step

## Consequences

- CLI uses Python's `argparse` (no additional dependency)
- JSON output to stdout enables scripting; human-readable summary to stderr
- Exit code 0 = passed, exit code 1 = failed, exit code 2 = error (no barcodes found, bad file, etc.)
