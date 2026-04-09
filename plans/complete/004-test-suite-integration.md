# EPIC 4: Test Suite & Integration Tests

## Context

Epics 1–3 delivered the full pipeline with 166 passing tests built TDD-style. EPIC 4 fills coverage gaps: ground-truth integration tests against all `test_docs/` files, unit edge cases, CLI batch integration, and error path hardening.

**Branch:** `feat/epic-004-test-suite`

---

## Phase 0: Ground-Truth Registry (sequential, one agent)

All streams depend on this. Must land first.

### Modify: `tests/conftest.py`

Add a `GROUND_TRUTH` dict mapping each `test_docs/` file to expected barcodes. User fills in `TODO` placeholders before running.

```python
GROUND_TRUTH = {
    "(proof)(BL6)(540841).pdf": {
        "barcodes": [
            {"value": "0850031591271", "type": "EAN_13", "symbology": "EAN13"},
        ],
    },
    "(proof)(BL6)(540837).pdf": {
        # TODO: User fills in — currently decodes as [] but may have barcodes
        "barcodes": [],
    },
    "EXCEL PRINTPACK-0480-01 proof.pdf": {
        # TODO: User fills in barcode values, types, symbologies
        "barcodes": [],
    },
    "EXCEL PRINTPACK-0480-04 proof.pdf": {
        # TODO: User fills in barcode values, types, symbologies
        "barcodes": [],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai": {
        # TODO: User fills in — likely same as .jpg (X004781QUF)
        "barcodes": [],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg": {
        "barcodes": [
            {"value": "X004781QUF", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
}
```

Also add a fixture:

```python
@pytest.fixture
def ground_truth():
    return GROUND_TRUTH
```

### Verify

- `uv run pytest tests/test_integration.py -v` — existing tests still pass (no breaking changes to conftest)

---

## Phase 1: Three Parallel Streams

After Phase 0 is committed, these three streams execute simultaneously. Each touches different test files.

---

### Stream A: Integration Test Expansion

**Modify:** `tests/test_integration.py`

Add a new test class `TestGroundTruth` that parametrizes over `GROUND_TRUTH`:

#### Tests to add:

1. **`test_validate_label_ground_truth[<file>]`** — For each file in GROUND_TRUTH with non-empty barcodes:
   - `validate_label(file)` succeeds without error
   - Number of barcodes decoded matches expected count
   - Each expected barcode value is present in results
   - Each expected barcode has correct `barcode_type`
   - Each expected barcode has correct `symbology`
   - `mode == "decode"`, `passed` is `True` (assuming valid barcodes)

2. **`test_validate_label_comparison_ground_truth[<file>]`** — For each file with non-empty barcodes:
   - `validate_label(file, expected_barcodes=[...all ground truth values...])` → `passed=True`
   - `expected_not_found == []`

3. **`test_validate_label_runs_without_error[<file>]`** — For ALL files (including those with empty barcodes):
   - `validate_label(file)` completes without exception
   - Returns a `ValidationResult`

4. **`test_to_json_schema_all_files[<file>]`** — For each file:
   - `.to_json()` produces valid JSON
   - All PRD fields present: `file`, `passed`, `mode`, `barcodes`, `expected_not_found`, `summary`
   - Each barcode dict has: `value`, `type`, `symbology`, `page`, `valid_format`, `valid_checkdigit`, `matches_expected`

#### Implementation notes:

- Use `pytest.mark.parametrize` with file names from `GROUND_TRUTH.keys()`
- Skip files that don't exist in `test_docs/` (same pattern as existing `pytestmark`)
- Import `GROUND_TRUTH` from `conftest` (or access via fixture)
- Keep existing `TestPDFProofs`, `TestAIFiles`, `TestRasterImages`, `TestValidateLabel` classes untouched

**Deps:** Phase 0 (GROUND_TRUTH dict). No source changes.

---

### Stream B: Unit Test Edge Cases

**Modify multiple existing test files.** No new files.

#### `tests/test_checkdigit.py` — Add:

```python
class TestMod10EdgeCases:
    def test_mod10_upce_invalid(self):
        assert _mod10_check("01234560") is False

    def test_mod10_single_digit(self):
        # Edge: single digit string
        assert isinstance(_mod10_check("0"), bool)

    def test_mod10_all_zeros(self):
        assert _mod10_check("0000000000000") is True  # 13 zeros, valid GTIN

class TestValidateCheckdigitEdge:
    def test_code39_returns_none(self):
        assert validate_checkdigit("HELLO", BarcodeType.CODE39) is None
```

#### `tests/test_classifier.py` — Add:

```python
def test_classify_isbn13_979_prefix():
    """979 prefix should also classify as ISBN_13."""
    result = classify(_barcode("9791234567890", "EAN13"))
    assert result is BarcodeType.ISBN_13

def test_classify_code39_symbology():
    result = classify(_barcode("HELLO-123", "Code39"))
    assert result is BarcodeType.CODE39

def test_classify_empty_value():
    """Empty value with unknown symbology."""
    result = classify(_barcode("", "Unknown"))
    assert result is BarcodeType.UNKNOWN

def test_classify_asin_lowercase_rejected():
    """ASIN pattern is uppercase only — lowercase B0 should not match."""
    result = classify(_barcode("b08N5WRWNW", "Code128"))
    assert result is not BarcodeType.ASIN
```

#### `tests/test_formatvalidator.py` — Add:

```python
class TestFormatEAN8Negative:
    def test_format_ean8_too_long(self):
        assert validate_format("123456789", BarcodeType.EAN_8) is False

    def test_format_ean8_alpha(self):
        assert validate_format("1234567A", BarcodeType.EAN_8) is False

class TestFormatUPCENegative:
    def test_format_upce_too_short(self):
        assert validate_format("1234567", BarcodeType.UPC_E) is False

class TestFormatCode39Negative:
    def test_format_code39_special_chars(self):
        assert validate_format("HELLO@WORLD", BarcodeType.CODE39) is False

class TestFormatASINNegative:
    def test_format_asin_too_short(self):
        assert validate_format("B08N5WRW", BarcodeType.ASIN) is False

    def test_format_asin_lowercase(self):
        assert validate_format("b08n5wrwnw", BarcodeType.ASIN) is False
```

#### `tests/test_validator.py` — Add:

```python
class TestValidateBarcodesEdge:
    def test_multiple_barcodes_mixed_types(self):
        """Multiple barcodes of different types in one file."""
        decoded = [
            DecodedBarcode("X004781QUF", "Code128", 1),
            DecodedBarcode("0850031591271", "EAN13", 1),
        ]
        result = validate_barcodes(decoded, "test.pdf")
        assert result.passed is True
        types = {b.barcode_type for b in result.barcodes}
        assert BarcodeType.FNSKU in types
        assert BarcodeType.EAN_13 in types

    def test_multiple_barcodes_one_invalid(self):
        """One valid, one invalid check digit → passed=False."""
        decoded = [
            DecodedBarcode("X004781QUF", "Code128", 1),
            DecodedBarcode("0850031591270", "EAN13", 1),  # bad checkdigit
        ]
        result = validate_barcodes(decoded, "test.pdf")
        assert result.passed is False

    def test_comparison_partial_match(self):
        """Some expected found, some not → passed=False."""
        decoded = [DecodedBarcode("X004781QUF", "Code128", 1)]
        result = validate_barcodes(
            decoded, "test.pdf",
            expected_barcodes=["X004781QUF", "NOTHERE"],
        )
        assert result.passed is False
        assert "NOTHERE" in result.expected_not_found
        bc = next(b for b in result.barcodes if b.value == "X004781QUF")
        assert bc.matches_expected is True

    def test_summary_contains_count(self):
        decoded = [
            DecodedBarcode("X004781QUF", "Code128", 1),
            DecodedBarcode("0850031591271", "EAN13", 2),
        ]
        result = validate_barcodes(decoded, "test.pdf")
        assert "2" in result.summary
```

**Deps:** None. Pure unit tests against existing source.

---

### Stream C: CLI Integration & Error Paths

**Modify:** `tests/test_cli_integration.py`

#### CLI batch tests — Add:

```python
class TestBatchRealFiles:
    """Batch mode with multiple real files."""

    def test_batch_two_pdfs(self, capsys):
        pdf1 = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        pdf2 = str(TEST_DOCS / "(proof)(BL6)(540837).pdf")
        code = main([pdf1, pdf2])
        assert code in (0, 1)  # depends on whether 540837 has barcodes

    def test_batch_pdf_and_jpg(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        jpg = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg")
        code = main([pdf, jpg])
        assert code == 0

    def test_batch_json_multiple_files(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        jpg = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg")
        code = main([pdf, jpg, "--json"])
        captured = capsys.readouterr()
        # Each file should produce JSON output
        assert "0850031591271" in captured.out
        assert "X004781QUF" in captured.out

    def test_batch_mixed_valid_and_error(self, capsys, unsupported_file):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([str(unsupported_file), pdf, "--json"])
        assert code == 2
        captured = capsys.readouterr()
        # Good file still processed
        assert "0850031591271" in captured.out
        assert "Error" in captured.err
```

#### AI file through CLI — Add:

```python
class TestAIFileCLI:
    def test_ai_file_decode(self, capsys):
        ai = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai")
        code = main([ai])
        assert code in (0, 1)  # depends on decode success

    def test_ai_file_json(self, capsys):
        ai = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai")
        code = main([ai, "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "file" in data
        assert "barcodes" in data
```

#### Error paths through validate_label — Add to `tests/test_integration.py`:

```python
class TestValidateLabelErrors:
    """Error paths through the full validate_label API."""

    def test_validate_label_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            validate_label("nonexistent.pdf")

    def test_validate_label_unsupported_format(self, unsupported_file):
        with pytest.raises(ValueError, match="Unsupported"):
            validate_label(unsupported_file)
```

**Deps:** None for unit/CLI tests. `unsupported_file` fixture already exists in conftest.

---

## Dependency Graph

```
Phase 0:  [conftest.py GROUND_TRUTH]
               |
    ┌──────────┼──────────┐
    v          v          v
  Stream A   Stream B   Stream C
  integration  unit      CLI +
  expansion    edges     error paths
    |          |          |
    └──────────┴──────────┘
               |
               v
         [User fills TODO placeholders]
               |
               v
         [uv run pytest — all green]
```

---

## User Action Required

After Phase 0 + Phase 1 are implemented, the user must:

1. Open `tests/conftest.py`
2. Fill in `GROUND_TRUTH` entries marked with `# TODO`
3. Run `uv run pytest` to verify

---

## Verification

1. `uv run pytest` — all existing + new tests pass
2. Every `test_docs/` file has at least one `validate_label()` integration test
3. Ground-truth barcodes match actual file contents (user-verified)
4. CLI batch mode works with mixed file types
5. Error paths (missing file, unsupported format) tested through `validate_label()` and CLI
6. No network required
