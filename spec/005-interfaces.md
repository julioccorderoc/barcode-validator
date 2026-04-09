# ADR-005: CLI and Programmatic Interfaces

## Status

Accepted

## Context

Two interfaces needed: CLI (primary, used by ops team + AI agent skill) and Python API (programmatic integration).

## Decision

### Python API

```python
from barcode_validator import validate_label

# Decode-only
result = validate_label(file_path="label_proof.pdf")

# Comparison
result = validate_label(
    file_path="label_proof.pdf",
    expected_barcodes=["X001ABC123"],
)

# result.barcodes -> detected barcodes with type, value, validation
# result.passed -> bool
# result.summary -> str
# result.to_json() -> JSON per PRD schema
```

### CLI (wraps Python API)

```bash
barcode-validator label_proof.pdf                          # decode-only
barcode-validator label_proof.pdf --expected X001ABC123    # comparison
barcode-validator label_proof.pdf --expected X001ABC123 --expected 012345678905
barcode-validator label_proof.pdf --json                   # JSON stdout
barcode-validator label_proof.ai --expected X001ABC123     # AI file
barcode-validator *.pdf --expected X001ABC123              # batch
```

### Output schema

Defined in `docs/PRD.md` > Output Schema. Canonical reference.

### CLI primary because

- AI agent skill invokes as CLI command
- Natural interface for ops team
- Python API for deeper integration, CLI = stable contract

### Two modes because

- **Decode-only:** "what's on this label?"
- **Comparison:** "is this the right barcode?" (main workflow)
- Same pipeline, comparison = optional final step

## Consequences

- CLI via `argparse` (no extra dep)
- JSON stdout, human summary stderr
- Exit: 0=pass, 1=fail, 2=error
