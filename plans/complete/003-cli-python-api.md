# EPIC-003: CLI & Python API

## Context

EPIC-001 (decoding) and EPIC-002 (classification/validation) are complete. The Python API already works: `validate_label()` accepts a file path and optional expected barcodes, returns a `ValidationResult` with `to_json()`. **EPIC-003 adds the CLI wrapper** so the ops team and AI agents can invoke validation from the command line.

The CLI is a thin layer over existing code. ADR-005 specifies: argparse, `--expected` (repeatable), `--json` flag, exit codes 0/1/2, JSON to stdout, human summary to stderr, batch support.

**Success criteria 3 and 4 are already met** (Python API works, `to_json()` produces valid JSON). This plan covers criteria 1, 2, and 5.

---

## Phase 0: Baseline Confirmation (sequential)

**Purpose:** Confirm all existing tests pass before starting.

**Actions:**
1. `uv run pytest` — verify all ~113 tests green
2. Add CLI test fixtures to `tests/conftest.py`:
   - `unsupported_file(tmp_path)` — creates a temp `.eps` file
   - `missing_file` — returns `Path("nonexistent.pdf")`

**Files modified:**
- `tests/conftest.py`

---

## Phase 1: Three Parallel Streams

Each stream creates a **separate source file + separate test file**. No cross-dependencies between streams during development.

### Stream A: Argument Parser

**Files:** `src/barcode_validator/cli_parser.py` + `tests/test_cli_parser.py`

**Public API:**
```python
def build_parser() -> argparse.ArgumentParser: ...
def parse_args(argv: list[str] | None = None) -> argparse.Namespace: ...
```

**Spec (from ADR-005):**
- Positional `files`: `nargs="+"`, one or more file paths
- `--expected`: `action="append"`, default `None` (not empty list)
- `--json`: `action="store_true"`, default `False`
- Program name: `barcode-validator`

**Tests (TDD):**
- Single file parses correctly
- Multiple files parse correctly
- `--expected` once → `["X001ABC123"]`
- `--expected` twice → `["X001ABC123", "012345678905"]`
- No `--expected` → `None`
- `--json` flag → `True`; absent → `False`
- No files → `SystemExit`
- Paths with spaces/parens parse correctly

**Dependencies:** `argparse` only (stdlib). No project imports.

---

### Stream B: Output Formatter

**Files:** `src/barcode_validator/cli_format.py` + `tests/test_cli_format.py`

**Public API:**
```python
def format_human(result: ValidationResult) -> str: ...
def format_json(result: ValidationResult) -> str: ...
def format_error(file_path: str, error: Exception) -> str: ...
```

**`format_human` output shape:**
```
File: label_proof.pdf
Mode: decode | Passed: true
Barcodes:
  [1] 0850031591271  EAN_13  (format: OK, checkdigit: OK)
  [2] X004781QUF     FNSKU   (format: OK)
Summary: All barcodes valid.
```

**`format_json`:** Delegates to `result.to_json()`.

**`format_error`:** Returns `"Error: {file_path}: {error}"`.

**Tests (TDD):**
- Construct `ValidationResult` manually in tests
- `format_human` contains file name, mode, pass/fail, barcode values
- `format_human` decode-only: no `matches_expected` column
- `format_human` comparison mode: shows match status
- `format_human` empty barcodes: still renders cleanly
- `format_json` returns valid JSON matching `result.to_json()`
- `format_error` includes file path and error message

**Dependencies:** Imports `ValidationResult`, `BarcodeResult`, `BarcodeType` from `models.py` only. No dependency on Stream A or C.

---

### Stream C: Main CLI Orchestrator

**Files:** `src/barcode_validator/cli.py` + `tests/test_cli.py`

**Public API:**
```python
def main(argv: list[str] | None = None) -> int: ...
```

**Logic:**
1. `args = parse_args(argv)`
2. `exit_code = 0`
3. For each file in `args.files`:
   - Try: `result = validate_label(file, expected_barcodes=args.expected)`
   - If `args.json`: print `format_json(result)` to stdout
   - Else: print `format_human(result)` to stderr
   - If not `result.passed`: `exit_code = max(exit_code, 1)`
   - Catch `(FileNotFoundError, ValueError)`: print `format_error(...)` to stderr, `exit_code = max(exit_code, 2)`
4. Return `exit_code`

**Tests (TDD) — mock `validate_label` via `monkeypatch`:**
- Single file, passes → exit 0, human output to stderr
- Single file, fails → exit 1
- `--json` flag → JSON to stdout
- `--expected` match → exit 0
- `--expected` mismatch → exit 1, `expected_not_found` in output
- Missing file → exit 2, error to stderr
- Unsupported format → exit 2, error to stderr
- Batch: two files both pass → exit 0
- Batch: one fails, one passes → exit 1
- Batch: one errors → exit 2 (error trumps fail)

**Dependencies:** Imports `parse_args` from `cli_parser`, formatters from `cli_format`, `validate_label` from `barcode_validator`. Tests mock all three to stay independent.

---

## Phase 2: Entry Points & Integration (sequential)

After all Phase 1 streams are complete.

### 2a: Package Entry Points

**Create `src/barcode_validator/__main__.py`:**
```python
import sys
from barcode_validator.cli import main
sys.exit(main())
```

**Modify `pyproject.toml`** — add `[project.scripts]`:
```toml
[project.scripts]
barcode-validator = "barcode_validator.cli:main"
```

Run `uv sync` to register the entry point.

### 2b: Integration Tests

**Create `tests/test_cli_integration.py`** — real files, no mocks.

**Tests (skip if `test_docs/` missing):**
- `main(["(proof)(BL6)(540841).pdf"])` → exit 0, stderr has barcode values
- `main(["(proof)(BL6)(540841).pdf", "--json"])` → exit 0, stdout is valid PRD-schema JSON
- `main(["(proof)(BL6)(540841).pdf", "--expected", "0850031591271"])` → exit 0
- `main(["(proof)(BL6)(540841).pdf", "--expected", "WRONG"])` → exit 1
- `main(["nonexistent.pdf"])` → exit 2
- Unsupported file → exit 2
- `python -m barcode_validator --help` via subprocess → exit 0

---

## Dependency Graph

```
Phase 0:  [conftest fixtures]
               |
    ┌──────────┼──────────┐
    v          v          v
Phase 1:  Stream A     Stream B     Stream C
          cli_parser   cli_format   cli.py
          (no deps)    (models)     (mocks A+B)
    |          |          |
    └──────────┴──────────┘
               |
               v
Phase 2:  [__main__.py + pyproject.toml + integration tests]
```

## Files Summary

| Phase | File | Action |
|-------|------|--------|
| 0 | `tests/conftest.py` | Modify |
| 1A | `src/barcode_validator/cli_parser.py` | Create |
| 1A | `tests/test_cli_parser.py` | Create |
| 1B | `src/barcode_validator/cli_format.py` | Create |
| 1B | `tests/test_cli_format.py` | Create |
| 1C | `src/barcode_validator/cli.py` | Create |
| 1C | `tests/test_cli.py` | Create |
| 2 | `src/barcode_validator/__main__.py` | Create |
| 2 | `tests/test_cli_integration.py` | Create |
| 2 | `pyproject.toml` | Modify |

## Verification

After Phase 2, confirm all EPIC-003 success criteria:

1. `barcode-validator test_docs/"(proof)(BL6)(540841).pdf"` → barcodes to stderr, JSON with `--json`
2. `barcode-validator test_docs/*.pdf --expected X001ABC123` → exit 0/1
3. `from barcode_validator import validate_label` → works (already done)
4. `result.to_json()` → valid JSON (already done)
5. Invalid/unsupported files → exit 2

Final: `uv run pytest` — all tests pass (existing + new CLI tests).
