# ROADMAP

- Version: 0.1.0
- Last Updated: 2026-04-09
- Owner: Julio Cordero

## Planner Rules

1. One Epic `Active` at a time.
2. Verify all Success Criteria met in main before marking `Complete`.
3. Don't start Epics with incomplete prerequisites.

## Epic Ledger

### EPIC-001: Core Decoding Pipeline

- Status: Complete
- Dependencies: None
- **Goal:** Accept label proofs (PDF, AI, PSD, PNG, JPG, TIFF, BMP), decode all barcodes, output raw values + symbology metadata. Foundation for everything else.
- **Scope:** File format routing (ADR-006), PDF/AI render via PyMuPDF at 2x (ADR-002), PSD/raster via Pillow, zxing-cpp primary + pyzbar fallback (ADR-001), OpenCV preprocessing retry (ADR-003). Output = list of raw decoded barcode objects. No classification, validation, or CLI.
- **Done when:**
  - PDF from `test_docs/` → all barcodes decoded with correct values + symbology
  - Raster image (PNG/JPG) barcode decoded correctly
  - zxing-cpp miss → preprocessing retry succeeds
  - AI (PDF-compatible) and PSD (flattened) handled without error
  - Unsupported extensions → clear error message

### EPIC-002: Classification, Validation & Report Output

- Status: Complete
- Dependencies: EPIC-001
- **Goal:** Classify decoded barcodes by type (FNSKU, UPC-A, EAN-13, etc.), validate format + check digits, compare against expected values, produce JSON output per PRD schema.
- **Scope:** Pattern matching classification (ADR-004), MOD-10 check digit for UPC/EAN/ISBN, regex format validation, decode-only vs comparison mode, JSON output schema. Consumes EPIC-001 output → produces `ValidationResult` with `to_json()`. No CLI.
- **Done when:**
  - FNSKU (X00, Code 128) classified correctly, `valid_format: true`
  - UPC-A correct check digit → `valid_checkdigit: true`; corrupted → `false`
  - Comparison mode: correct expected → `passed: true`; wrong → `passed: false` + `expected_not_found`
  - Decode-only: `matches_expected` is `null`, `passed` from format/checkdigit only
  - JSON matches PRD schema

### EPIC-003: CLI & Python API

- Status: Complete
- Dependencies: EPIC-002
- **Goal:** CLI for ops team + AI agents, Python API for programmatic use. End-to-end usability.
- **Scope:** argparse CLI with file path, `--expected`, `--json` (ADR-005). `validate_label()` entry point. Exit codes: 0=pass, 1=fail, 2=error. JSON stdout, human stderr. Batch support. Package entrypoint in `pyproject.toml`. Project root = skill directory. No GUI.
- **Done when:**
  - `barcode-validator test_docs/"(proof)(BL6)(540841).pdf"` → decoded barcodes stderr, JSON stdout
  - `barcode-validator test_docs/*.pdf --expected X001ABC123` → exit 0 match, exit 1 mismatch
  - `from barcode_validator import validate_label` works, returns `ValidationResult`
  - `result.to_json()` → valid PRD-schema JSON
  - Exit 2 for invalid/unsupported files

### EPIC-004: Test Suite & Integration Tests

- Status: Complete
- Dependencies: EPIC-001 (unit tests alongside), EPIC-003 (integration tests)
- **Goal:** Correctness + regression prevention. Real proofs in `test_docs/` as ground-truth.
- **Scope:** pytest. Unit tests per layer: routing, rendering, decoding, classification, check digits, regex, comparison, JSON. Integration tests = full pipeline against real proofs. Offline only. Fixtures: `(proof)(BL6)(540837).pdf` and `(proof)(BL6)(540841).pdf`.
- **Done when:**
  - `pytest` all green *(208 passed, 8 xfailed)*
  - Unit coverage: check digits (correct/incorrect), classification per type, decode-only vs comparison, error paths
  - Integration: `validate_label()` against each `test_docs/` PDF → known barcodes decoded + classified + validated
  - No network required
- **Note:** 4 test_docs files have barcodes the decoder fails to extract (marked xfail). Tracked in `ERRORS.md`.

### EPIC-005: AI Agent Skill Definition (`SKILL.md`)

- Status: Planned
- Dependencies: EPIC-003
- **Goal:** Make validator invocable as AI agent skill. Agents call it from conversation context.
- **Scope:** `SKILL.md` at project root with metadata (name, description, triggers, examples). Wraps CLI from EPIC-003. Clear input/output contracts. No new Python code — declarative only.
- **Done when:**
  - `SKILL.md` exists at root with valid frontmatter
  - Trigger conditions clear (validate barcode, check label proof)
  - Usage examples for decode-only + comparison modes
  - Agent can read `SKILL.md` and invoke correctly against `test_docs/`
