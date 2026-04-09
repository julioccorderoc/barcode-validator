# EPIC 2: Classification, Validation & Report Output

## Context

EPIC 1 delivered the core decoding pipeline: `File → load_images() → decode_barcodes() → list[DecodedBarcode]`. EPIC 2 extends this to classify barcodes by type, validate format + check digits, compare against expected values, and produce the PRD JSON output schema. This completes the validation logic before CLI wiring (EPIC 3).

**Branch:** `feat/epic-002-classification-validation`

---

## Phase 0: Shared Types (sequential, one agent)

Extend `src/barcode_validator/models.py` with EPIC 2 types. All parallel streams import these, so this must land first.

### Add to `models.py`

```python
class BarcodeType(Enum):
    FNSKU = "FNSKU"
    ISBN_13 = "ISBN_13"
    UPC_A = "UPC_A"
    EAN_13 = "EAN_13"
    EAN_8 = "EAN_8"
    UPC_E = "UPC_E"
    ASIN = "ASIN"
    CODE128 = "CODE128"
    CODE39 = "CODE39"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class BarcodeResult:
    value: str
    barcode_type: BarcodeType
    symbology: str
    page: int
    valid_format: bool
    valid_checkdigit: bool | None   # None for types without check digits
    matches_expected: bool | None   # None in decode-only mode

@dataclass(frozen=True)
class ValidationResult:
    file: str
    passed: bool
    mode: str                       # "decode" | "comparison"
    barcodes: list[BarcodeResult]
    expected_not_found: list[str]
    summary: str

    def to_dict(self) -> dict: ...
    def to_json(self) -> str: ...
```

### Tests (append to `tests/test_models.py`)

- BarcodeType enum has all 10 values, `.value` matches PRD strings
- BarcodeResult frozen, fields accessible
- ValidationResult.to_dict() shape matches PRD schema
- ValidationResult.to_json() produces valid JSON
- `valid_checkdigit=None` and `matches_expected=None` serialize to JSON `null`
- `barcode_type` serializes as string value, not `BarcodeType.X`

### Notes

- `to_dict()`: manual dict construction (not `dataclasses.asdict`) to control enum→string and field name mapping (`barcode_type` → `"type"` in JSON per PRD)
- `to_json()`: calls `to_dict()` then `json.dumps(indent=2)`

---

## Phase 1: Four Parallel Streams

After Phase 0 is committed, these four work units execute simultaneously. Each imports only from `models.py`.

### Stream 1: Classifier

**Create:** `src/barcode_validator/classifier.py` + `tests/test_classifier.py`

```python
def classify(barcode: DecodedBarcode) -> BarcodeType:
```

Priority-ordered pattern matching (ADR-004):

1. `^X00[A-Z0-9]{7}$` → FNSKU
2. `^\d{13}$` + prefix 978/979 → ISBN_13
3. `^\d{12}$` → UPC_A
4. `^\d{13}$` → EAN_13
5. `^\d{8}$` → EAN_8 or UPC_E (disambiguate: `"UPC"` in symbology → UPC_E, else EAN_8)
6. `^B0[A-Z0-9]{8}$` → ASIN
7. symbology contains `"Code128"` → CODE128
8. symbology contains `"Code39"` → CODE39
9. else → UNKNOWN

**Key tests:**
- Each barcode type classified correctly with ground-truth values
- ISBN-13 wins over EAN-13 when 978/979 prefix (priority test)
- 8-digit disambiguation by symbology (EAN8 vs UPCE)
- FNSKU "X004781QUF" + symbology "Code128" → FNSKU (not CODE128, priority)
- Unknown symbology + random value → UNKNOWN

**Deps:** `models.py` only. Pure Python.

---

### Stream 2: Check Digit Validator

**Create:** `src/barcode_validator/checkdigit.py` + `tests/test_checkdigit.py`

```python
def validate_checkdigit(value: str, barcode_type: BarcodeType) -> bool | None:
def _mod10_check(digits: str) -> bool:
```

MOD 10 (GTIN) algorithm: alternating weights 1/3 from right, sum % 10 == 0.

| Type | Action |
|------|--------|
| UPC_A, EAN_13, EAN_8, ISBN_13, UPC_E | `_mod10_check(value)` |
| FNSKU, ASIN, CODE128, CODE39, UNKNOWN | return `None` |

**Key tests:**
- `"0850031591271"` (ground truth EAN-13) → True
- `"0850031591270"` (corrupted) → False
- `"012345678905"` (valid UPC-A) → True
- `"012345678900"` (invalid UPC-A) → False
- Valid ISBN-13, EAN-8, UPC-E → True
- FNSKU, ASIN, CODE128, UNKNOWN → None

**Deps:** `models.py` only. Pure Python.

---

### Stream 3: Format Validator

**Create:** `src/barcode_validator/formatvalidator.py` + `tests/test_formatvalidator.py`

```python
def validate_format(value: str, barcode_type: BarcodeType) -> bool:
```

Dict mapping `BarcodeType` → compiled regex:

| Type | Pattern |
|------|---------|
| FNSKU | `^X00[A-Z0-9]{7}$` |
| ISBN_13 | `^(978\|979)\d{10}$` |
| UPC_A | `^\d{12}$` |
| EAN_13 | `^\d{13}$` |
| EAN_8 | `^\d{8}$` |
| UPC_E | `^\d{8}$` |
| ASIN | `^B0[A-Z0-9]{8}$` |
| CODE128 | `^[\x20-\x7E]+$` (printable ASCII) |
| CODE39 | `^[A-Z0-9 \-.$/+%]+$` |
| UNKNOWN | `^.+$` (non-empty) |

**Key tests:**
- Ground truth values pass: "X004781QUF" FNSKU, "0850031591271" EAN-13
- Invalid prefix/length/chars fail for each type
- Empty string fails UNKNOWN

**Deps:** `models.py` only. Pure Python.

---

### Stream 4: Comparator

**Create:** `src/barcode_validator/comparator.py` + `tests/test_comparator.py`

```python
def match_expected(
    decoded_values: list[str],
    expected_values: list[str],
) -> tuple[dict[str, bool], list[str]]:
    """Returns (matches_dict, expected_not_found)."""
```

- `matches_dict[value] = value in expected_set` for each decoded value
- `expected_not_found = [e for e in expected if e not in decoded_set]`
- Exact string comparison, case-sensitive

**Key tests:**
- All matched → all True, empty not_found
- None matched → all False, all in not_found
- Partial match
- Extra decoded values (not in expected) → False
- Empty expected → all False, empty not_found
- Empty decoded → expected in not_found
- Case-sensitive: "x004781quf" ≠ "X004781QUF"

**Deps:** None. Pure Python.

---

## Phase 2: Integration (sequential, one agent)

After Phase 1 streams merge, wire everything together.

### Orchestrator

**Create:** `src/barcode_validator/validator.py` + `tests/test_validator.py`

```python
def validate_barcodes(
    decoded: list[DecodedBarcode],
    file_path: str,
    expected_barcodes: list[str] | None = None,
) -> ValidationResult:
```

**Flow:**
1. Mode: `"comparison"` if `expected_barcodes is not None`, else `"decode"`
2. If comparison: `matches_dict, not_found = match_expected(decoded_values, expected_barcodes)`
3. For each DecodedBarcode:
   - `barcode_type = classify(barcode)`
   - `valid_format = validate_format(barcode.value, barcode_type)`
   - `valid_checkdigit = validate_checkdigit(barcode.value, barcode_type)`
   - `matches_expected`: comparison → `matches_dict[value]`, decode → `None`
4. `passed`:
   - Decode-only: `all(b.valid_format and b.valid_checkdigit is not False for b in results)`
   - Comparison: `len(not_found) == 0 and all(b.matches_expected for b in results if b.matches_expected is not None)`
5. Build summary, return `ValidationResult`

**Tests (use hand-constructed DecodedBarcode lists, no file I/O):**
- Decode-only mode: mode="decode", matches_expected=None
- Comparison mode: mode="comparison", matches_expected populated
- Valid FNSKU decode-only → passed=True
- Invalid UPC-A check digit → passed=False
- Comparison all matched → passed=True
- Comparison missing expected → passed=False, expected_not_found populated
- Empty barcodes decode-only → passed=True (vacuous)
- Empty barcodes comparison with expected → passed=False
- JSON output matches PRD schema

### Public API Update

**Modify:** `src/barcode_validator/__init__.py`

```python
def validate_label(
    file_path: str | Path,
    expected_barcodes: list[str] | None = None,
) -> ValidationResult:
    pages = load_images(Path(file_path))
    decoded = decode_barcodes(pages)
    return validate_barcodes(decoded, str(file_path), expected_barcodes)
```

Update `__all__`: add `validate_label`, `ValidationResult`, `BarcodeResult`, `BarcodeType`.

### Integration Tests

**Modify:** `tests/test_integration.py` — add EPIC 2 test class:

- `validate_label("(proof)(BL6)(540841).pdf")` → EAN-13 classified, valid_checkdigit=True, mode="decode"
- `validate_label(..., expected_barcodes=["0850031591271"])` → passed=True
- `validate_label(..., expected_barcodes=["WRONG"])` → passed=False, expected_not_found=["WRONG"]
- `validate_label("...Level_Off.jpg")` → FNSKU classified, valid_format=True
- `.to_json()` output is valid JSON with all PRD fields

---

## Dependency Graph

```
Phase 0:  [models.py types]
               |
    ┌──────────┼──────────┬──────────┐
    v          v          v          v
Phase 1:  classifier  checkdigit  formatval  comparator
    |          |          |          |
    └──────────┴──────────┴──────────┘
               |
               v
Phase 2:  [validator.py + __init__.py + integration tests]
```

---

## Verification

1. `uv run pytest` — all existing + new tests pass
2. `validate_label("(proof)(BL6)(540841).pdf")` returns ValidationResult with correct EAN-13 classification
3. `validate_label(..., expected_barcodes=["0850031591271"]).passed` is `True`
4. `validate_label(..., expected_barcodes=["WRONG"]).passed` is `False`
5. `.to_json()` output matches PRD schema exactly
6. `decode_file()` still works unchanged (backwards compatible)
