# ROADMAP

- Version: 0.1.0
- Last Updated: 2026-04-09
- Primary Human Owner: Julio Cordero

## Operating Rules for the Planner Agent

1. You may only move one Epic to `Active` at a time.
2. Before marking an Epic `Complete`, you must verify all its Success Criteria are met in the main branch.
3. Do not parse or extract Epics that depend on incomplete prerequisites.

## Epic Ledger

### EPIC-001: Core Decoding Pipeline

- Status: Planned
- Dependencies: None
- Business Objective: Accept label proof files (PDF, AI, PSD, PNG, JPG, TIFF, BMP) and decode all barcodes present, producing raw decoded values and symbology metadata. This is the foundation every other feature depends on.
- Technical Boundary: File format routing (ADR-006), PDF/AI rendering via PyMuPDF at 2x scale (ADR-002), PSD/raster loading via Pillow, barcode decoding with zxing-cpp primary + optional pyzbar fallback (ADR-001), and the OpenCV preprocessing retry pipeline (ADR-003). Output is a list of raw decoded barcode objects (value, symbology, page number). No classification, validation, or CLI in this epic.
- Verification Criteria (Definition of Done):
  - Given a PDF label proof from `test_docs/`, all barcodes on every page are decoded with correct raw values and symbology reported.
  - Given a raster image (PNG/JPG) containing a barcode, the barcode is decoded correctly.
  - If the primary decoder (zxing-cpp) misses a barcode, the preprocessing pipeline (grayscale → blur → threshold) retries and the barcode is decoded on the second attempt.
  - AI files with PDF compatibility and PSD files with flattened composites are handled through their respective paths without error.
  - Unsupported file extensions return a clear error message.

### EPIC-002: Classification, Validation & Report Output

- Status: Planned
- Dependencies: EPIC-001
- Business Objective: Classify each decoded barcode by business type (FNSKU, UPC-A, EAN-13, ISBN-13, etc.), validate format and check digits, optionally compare against expected values, and produce the structured JSON output defined in the PRD. This is the intelligence layer that turns raw barcode data into actionable pass/fail results.
- Technical Boundary: Barcode type classification via priority-ordered pattern matching (ADR-004), MOD-10 check digit validation for UPC/EAN/ISBN, regex format validation for all types, decode-only vs. comparison mode logic, and the JSON output schema (PRD Output Schema). Consumes raw decoded barcodes from EPIC-001 and produces `ValidationResult` dataclass with `to_json()`. No CLI or user-facing interface in this epic.
- Verification Criteria (Definition of Done):
  - An FNSKU barcode (X00 prefix, Code 128) from `test_docs/` is classified as `FNSKU` with `valid_format: true`.
  - A UPC-A barcode with a correct check digit returns `valid_checkdigit: true`; a corrupted digit returns `valid_checkdigit: false`.
  - In comparison mode, providing the correct expected value returns `matches_expected: true` and `passed: true`; a wrong expected value returns `matches_expected: false` and `passed: false` with the value listed in `expected_not_found`.
  - In decode-only mode, `matches_expected` is `null` and `passed` reflects format/check digit validity only.
  - JSON output matches the schema defined in the PRD (all fields present, correct types).

### EPIC-003: CLI & Python API

- Status: Planned
- Dependencies: EPIC-002
- Business Objective: Expose the full pipeline through a CLI for the operations team and AI agent skill invocation, and a Python API for programmatic integration. This makes the tool usable end-to-end.
- Technical Boundary: CLI via argparse with file path, `--expected`, `--json` flags (ADR-005). Python API via `validate_label()` entry-point function. Exit codes: 0 = passed, 1 = failed, 2 = error. JSON to stdout, human-readable summary to stderr. Batch support for multiple files. Package entrypoint in `pyproject.toml`. The project root **is** the skill directory (no subdirectory nesting). No web UI or GUI.
- Verification Criteria (Definition of Done):
  - `barcode-validator test_docs/"(proof)(BL6)(540841).pdf"` runs end-to-end and prints decoded barcodes to stderr with JSON to stdout.
  - `barcode-validator test_docs/*.pdf --expected X001ABC123` runs comparison mode across multiple files, exits 0 on match and 1 on mismatch.
  - `from barcode_validator import validate_label; result = validate_label("test_docs/(proof)(BL6)(540841).pdf")` returns a `ValidationResult` with correct fields.
  - `result.to_json()` produces valid JSON matching the PRD schema.
  - Exit code 2 is returned for invalid/unsupported files.

### EPIC-004: Test Suite & Integration Tests

- Status: Planned
- Dependencies: EPIC-001 (unit tests can begin alongside EPIC-001; integration tests require EPIC-003)
- Business Objective: Ensure correctness and prevent regressions across the entire pipeline. Real label proofs in `test_docs/` serve as ground-truth fixtures for end-to-end validation.
- Technical Boundary: pytest test suite. Unit tests for each layer: file format routing, PDF rendering, barcode decoding, classification logic, check digit algorithms, format regex patterns, comparison logic, and JSON serialization. Integration tests run the full pipeline against real label proofs in `test_docs/`. Tests must run offline with no network access. Test fixtures include the two real NCL label proofs: `(proof)(BL6)(540837).pdf` and `(proof)(BL6)(540841).pdf`.
- Verification Criteria (Definition of Done):
  - `pytest` passes with all tests green.
  - Unit tests cover: check digit validation (correct/incorrect), format classification for every supported barcode type, decode-only vs. comparison mode output, error paths (unsupported file, no barcodes found).
  - Integration tests run `validate_label()` against each PDF in `test_docs/` and assert that known barcodes are decoded, classified, and validated correctly.
  - No test requires network access.

### EPIC-005: AI Agent Skill Definition (`SKILL.md`)

- Status: Planned
- Dependencies: EPIC-003
- Business Objective: Make the barcode validator invocable as an AI agent skill so that agents (e.g., Claude Code) can call it directly from conversation context. The project root is the skill directory — `SKILL.md` lives at the repo root alongside the code.
- Technical Boundary: Author `SKILL.md` at the project root with skill metadata (name, description, trigger conditions, usage examples). The skill wraps the CLI interface defined in EPIC-003. Define clear input/output contracts so an agent knows when and how to invoke barcode validation. No new Python code — this is a declarative skill definition that points to the existing CLI/API.
- Verification Criteria (Definition of Done):
  - `SKILL.md` exists at the project root with valid skill frontmatter (name, description).
  - The skill description clearly states trigger conditions (e.g., user asks to validate a barcode, check a label proof).
  - Usage examples demonstrate both decode-only and comparison modes.
  - An AI agent can read `SKILL.md` and invoke the tool correctly against a `test_docs/` file.
