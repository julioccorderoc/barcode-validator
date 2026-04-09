# Public Barcode Lookup Extension — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add pluggable public barcode lookup that enriches decoded barcodes with product info from free APIs (Open Food Facts, UPCitemdb).

**Architecture:** `LookupProvider` ABC with `LookupService` orchestrator. Two built-in providers ship by default. Integrates after validation, before JSON output. `--no-lookup` CLI flag disables all network calls.

**Tech Stack:** Python 3.13+, `urllib.request` (stdlib — no new dependencies), pytest with `unittest.mock` for HTTP mocking.

**Spec:** `docs/superpowers/specs/2026-04-09-public-barcode-lookup-design.md`

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `src/barcode_validator/lookup.py` | `LookupResult` dataclass, `LookupProvider` ABC, `OpenFoodFactsProvider`, `UPCitemdbProvider`, `LookupService` |
| Create | `tests/test_lookup.py` | Unit tests for all lookup components (mocked HTTP) |
| Modify | `src/barcode_validator/models.py` | Add `lookup` field to `BarcodeResult`, update `to_dict()` in `ValidationResult` |
| Modify | `src/barcode_validator/validator.py` | Accept `lookup_service` param, call lookup per barcode |
| Modify | `src/barcode_validator/__init__.py` | Pass `lookup_service` to `validate_barcodes()`, export new types |
| Modify | `src/barcode_validator/cli_parser.py` | Add `--no-lookup` flag |
| Modify | `src/barcode_validator/cli.py` | Wire `--no-lookup` into `validate_label()` |
| Modify | `src/barcode_validator/cli_format.py` | Show lookup info in human-readable output |
| Modify | `tests/test_validator.py` | Update existing tests for new `lookup` field |
| Modify | `tests/test_models.py` | Update existing tests for new `lookup` field |
| Modify | `tests/test_cli_parser.py` | Test `--no-lookup` flag |
| Modify | `tests/test_cli.py` | Update for lookup integration |
| Modify | `tests/test_cli_format.py` | Update for lookup in human output |
| Modify | `tests/test_integration.py` | Ensure existing tests pass with `lookup: None` |
| Modify | `docs/PRD.md` | Relax offline constraint for extensions |
| Modify | `SKILL.md` | Document `--no-lookup`, update examples |
| Modify | `pyproject.toml` | Add `network` pytest marker |

---

### Task 1: Add `LookupResult` dataclass and `lookup` field to `BarcodeResult`

**Files:**
- Modify: `src/barcode_validator/models.py`
- Modify: `tests/test_models.py`

- [ ] **Step 1: Write failing test for `LookupResult` dataclass**

In `tests/test_models.py`, add:

```python
from barcode_validator.models import LookupResult


def test_lookup_result_found():
    result = LookupResult(
        found=True,
        product_name="Test Product",
        brand="Test Brand",
        category="Food",
        source="test_provider",
    )
    assert result.found is True
    assert result.product_name == "Test Product"
    assert result.brand == "Test Brand"
    assert result.category == "Food"
    assert result.source == "test_provider"


def test_lookup_result_not_found():
    result = LookupResult(
        found=False,
        product_name=None,
        brand=None,
        category=None,
        source=None,
    )
    assert result.found is False
    assert result.product_name is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_models.py::test_lookup_result_found -v`
Expected: FAIL — `ImportError: cannot import name 'LookupResult'`

- [ ] **Step 3: Implement `LookupResult` in `models.py`**

Add after the `BarcodeType` enum in `src/barcode_validator/models.py`:

```python
@dataclass(frozen=True)
class LookupResult:
    """Product information from a public barcode database."""
    found: bool
    product_name: str | None
    brand: str | None
    category: str | None
    source: str | None
```

- [ ] **Step 4: Add `lookup` field to `BarcodeResult`**

Change `BarcodeResult` in `src/barcode_validator/models.py`. Add a `lookup` field with default `None`:

```python
@dataclass(frozen=True)
class BarcodeResult:
    """A classified and validated barcode."""
    value: str
    barcode_type: BarcodeType
    symbology: str
    page: int
    valid_format: bool
    valid_checkdigit: bool | None
    matches_expected: bool | None
    lookup: LookupResult | None = None
```

- [ ] **Step 5: Update `ValidationResult.to_dict()` to include lookup**

In `src/barcode_validator/models.py`, update the barcode dict comprehension inside `to_dict()`:

```python
"barcodes": [
    {
        "value": b.value,
        "type": b.barcode_type.value,
        "symbology": b.symbology,
        "page": b.page,
        "valid_format": b.valid_format,
        "valid_checkdigit": b.valid_checkdigit,
        "matches_expected": b.matches_expected,
        "lookup": {
            "found": b.lookup.found,
            "product_name": b.lookup.product_name,
            "brand": b.lookup.brand,
            "category": b.lookup.category,
            "source": b.lookup.source,
        } if b.lookup is not None else None,
    }
    for b in self.barcodes
],
```

- [ ] **Step 6: Write test for `to_dict()` with lookup**

In `tests/test_models.py`, add:

```python
def test_validation_result_to_dict_with_lookup():
    lookup = LookupResult(
        found=True,
        product_name="Test Product",
        brand="Test Brand",
        category="Food",
        source="open_food_facts",
    )
    bc = BarcodeResult(
        value="012345678901",
        barcode_type=BarcodeType.UPC_A,
        symbology="EAN-13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
        lookup=lookup,
    )
    result = ValidationResult(
        file="test.pdf",
        passed=True,
        mode="decode",
        barcodes=[bc],
        expected_not_found=[],
        summary="1 barcode(s) found. All validations passed.",
    )
    d = result.to_dict()
    assert d["barcodes"][0]["lookup"]["found"] is True
    assert d["barcodes"][0]["lookup"]["product_name"] == "Test Product"
    assert d["barcodes"][0]["lookup"]["source"] == "open_food_facts"


def test_validation_result_to_dict_without_lookup():
    bc = BarcodeResult(
        value="012345678901",
        barcode_type=BarcodeType.UPC_A,
        symbology="EAN-13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
    )
    result = ValidationResult(
        file="test.pdf",
        passed=True,
        mode="decode",
        barcodes=[bc],
        expected_not_found=[],
        summary="1 barcode(s) found. All validations passed.",
    )
    d = result.to_dict()
    assert d["barcodes"][0]["lookup"] is None
```

- [ ] **Step 7: Run all model tests**

Run: `uv run pytest tests/test_models.py -v`
Expected: ALL PASS

- [ ] **Step 8: Run full test suite to check for regressions**

Run: `uv run pytest -v`
Expected: ALL PASS — existing tests should still work because `lookup` defaults to `None`.

- [ ] **Step 9: Commit**

```bash
git add src/barcode_validator/models.py tests/test_models.py
git commit -m "feat(epic-006): add LookupResult dataclass and lookup field to BarcodeResult"
```

---

### Task 2: Implement `LookupProvider` ABC and `LookupService`

**Files:**
- Create: `src/barcode_validator/lookup.py`
- Create: `tests/test_lookup.py`

- [ ] **Step 1: Write failing tests for `LookupService` with mock providers**

Create `tests/test_lookup.py`:

```python
"""Tests for the lookup module — providers and service."""

from barcode_validator.lookup import LookupProvider, LookupService
from barcode_validator.models import BarcodeType, LookupResult


class FakeProvider(LookupProvider):
    """Test provider that returns a fixed result."""

    def __init__(self, name: str, supported: set[BarcodeType], result: LookupResult | None):
        self._name = name
        self._supported = supported
        self._result = result

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_types(self) -> set[BarcodeType]:
        return self._supported

    def lookup(self, value: str) -> LookupResult | None:
        return self._result


FOUND_RESULT = LookupResult(
    found=True,
    product_name="Test Product",
    brand="Test Brand",
    category="Food",
    source="fake",
)


def test_service_returns_first_provider_hit():
    provider = FakeProvider("fake", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([provider])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is not None
    assert result.found is True
    assert result.product_name == "Test Product"


def test_service_skips_provider_that_does_not_support_type():
    provider = FakeProvider("fake", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([provider])
    result = service.lookup("X00ABC1234", BarcodeType.FNSKU)
    assert result is None


def test_service_tries_fallback_on_miss():
    miss = FakeProvider("miss", {BarcodeType.UPC_A}, None)
    hit = FakeProvider("hit", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([miss, hit])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is not None
    assert result.source == "fake"


def test_service_returns_none_when_all_miss():
    miss1 = FakeProvider("miss1", {BarcodeType.UPC_A}, None)
    miss2 = FakeProvider("miss2", {BarcodeType.UPC_A}, None)
    service = LookupService([miss1, miss2])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is None


def test_service_returns_none_for_empty_providers():
    service = LookupService([])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_lookup.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'barcode_validator.lookup'`

- [ ] **Step 3: Implement the ABC and service**

Create `src/barcode_validator/lookup.py`:

```python
"""Public barcode lookup — provider ABC and service orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod

from barcode_validator.models import BarcodeType, LookupResult


class LookupProvider(ABC):
    """Abstract base class for barcode lookup providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'open_food_facts')."""

    @property
    @abstractmethod
    def supported_types(self) -> set[BarcodeType]:
        """Barcode types this provider can look up."""

    @abstractmethod
    def lookup(self, value: str) -> LookupResult | None:
        """Look up a barcode value. Returns LookupResult or None if not found."""


class LookupService:
    """Orchestrates barcode lookups across multiple providers."""

    def __init__(self, providers: list[LookupProvider]) -> None:
        self._providers = providers

    def lookup(self, value: str, barcode_type: BarcodeType) -> LookupResult | None:
        """Look up a barcode value using registered providers.

        Tries providers in order. Returns the first hit, or None.
        """
        for provider in self._providers:
            if barcode_type not in provider.supported_types:
                continue
            result = provider.lookup(value)
            if result is not None:
                return result
        return None
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_lookup.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/lookup.py tests/test_lookup.py
git commit -m "feat(epic-006): add LookupProvider ABC and LookupService orchestrator"
```

---

### Task 3: Implement `OpenFoodFactsProvider`

**Files:**
- Modify: `src/barcode_validator/lookup.py`
- Modify: `tests/test_lookup.py`

- [ ] **Step 1: Write failing tests for `OpenFoodFactsProvider`**

Add to `tests/test_lookup.py`:

```python
import json
from unittest.mock import patch, MagicMock

from barcode_validator.lookup import OpenFoodFactsProvider


def _mock_urlopen(response_data: dict, status: int = 200):
    """Create a mock for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


class TestOpenFoodFactsProvider:
    def test_supported_types(self):
        provider = OpenFoodFactsProvider()
        assert BarcodeType.UPC_A in provider.supported_types
        assert BarcodeType.EAN_13 in provider.supported_types
        assert BarcodeType.EAN_8 in provider.supported_types
        assert BarcodeType.FNSKU not in provider.supported_types
        assert BarcodeType.ASIN not in provider.supported_types

    def test_name(self):
        provider = OpenFoodFactsProvider()
        assert provider.name == "open_food_facts"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "status": 1,
            "product": {
                "product_name": "Organic Coconut Oil",
                "brands": "Nature's Best",
                "categories": "Oils, Coconut oils",
            },
        })
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0850031591271")
        assert result is not None
        assert result.found is True
        assert result.product_name == "Organic Coconut Oil"
        assert result.brand == "Nature's Best"
        assert result.category == "Oils, Coconut oils"
        assert result.source == "open_food_facts"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_not_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({"status": 0})
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0000000000000")
        assert result is None

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_network_error(self, mock_urlopen_fn):
        mock_urlopen_fn.side_effect = OSError("Network unreachable")
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0850031591271")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_lookup.py::TestOpenFoodFactsProvider -v`
Expected: FAIL — `ImportError: cannot import name 'OpenFoodFactsProvider'`

- [ ] **Step 3: Implement `OpenFoodFactsProvider`**

Add to `src/barcode_validator/lookup.py`, after the `LookupService` class:

```python
import json
from urllib.request import urlopen, Request


class OpenFoodFactsProvider(LookupProvider):
    """Lookup via Open Food Facts API (free, no auth)."""

    API_URL = "https://world.openfoodfacts.net/api/v2/product/{barcode}"

    @property
    def name(self) -> str:
        return "open_food_facts"

    @property
    def supported_types(self) -> set[BarcodeType]:
        return {BarcodeType.UPC_A, BarcodeType.EAN_13, BarcodeType.EAN_8}

    def lookup(self, value: str) -> LookupResult | None:
        """Query Open Food Facts for a barcode."""
        url = self.API_URL.format(barcode=value)
        request = Request(url, headers={"User-Agent": "barcode-validator/0.1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
        except (OSError, json.JSONDecodeError):
            return None

        if data.get("status") != 1:
            return None

        product = data.get("product", {})
        return LookupResult(
            found=True,
            product_name=product.get("product_name") or None,
            brand=product.get("brands") or None,
            category=product.get("categories") or None,
            source=self.name,
        )
```

Also move the `import json` to the top of the file (it's already there from the new code) and add the urllib import at the top:

```python
from urllib.request import urlopen, Request
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_lookup.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/lookup.py tests/test_lookup.py
git commit -m "feat(epic-006): implement OpenFoodFactsProvider"
```

---

### Task 4: Implement `UPCitemdbProvider`

**Files:**
- Modify: `src/barcode_validator/lookup.py`
- Modify: `tests/test_lookup.py`

- [ ] **Step 1: Write failing tests for `UPCitemdbProvider`**

Add to `tests/test_lookup.py`:

```python
from barcode_validator.lookup import UPCitemdbProvider


class TestUPCitemdbProvider:
    def test_supported_types(self):
        provider = UPCitemdbProvider()
        assert BarcodeType.UPC_A in provider.supported_types
        assert BarcodeType.EAN_13 in provider.supported_types
        assert BarcodeType.EAN_8 in provider.supported_types
        assert BarcodeType.UPC_E in provider.supported_types
        assert BarcodeType.ISBN_13 in provider.supported_types
        assert BarcodeType.FNSKU not in provider.supported_types

    def test_name(self):
        provider = UPCitemdbProvider()
        assert provider.name == "upcitemdb"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "code": "OK",
            "total": 1,
            "items": [{
                "title": "Coconut Oil Organic",
                "brand": "Nature's Best",
                "category": "Health & Beauty",
            }],
        })
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        assert result is not None
        assert result.found is True
        assert result.product_name == "Coconut Oil Organic"
        assert result.brand == "Nature's Best"
        assert result.category == "Health & Beauty"
        assert result.source == "upcitemdb"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_not_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "code": "OK",
            "total": 0,
            "items": [],
        })
        provider = UPCitemdbProvider()
        result = provider.lookup("0000000000000")
        assert result is None

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_network_error(self, mock_urlopen_fn):
        mock_urlopen_fn.side_effect = OSError("Connection refused")
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        assert result is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_lookup.py::TestUPCitemdbProvider -v`
Expected: FAIL — `ImportError: cannot import name 'UPCitemdbProvider'`

- [ ] **Step 3: Implement `UPCitemdbProvider`**

Add to `src/barcode_validator/lookup.py`:

```python
class UPCitemdbProvider(LookupProvider):
    """Lookup via UPCitemdb API (free tier, 100 req/day, no auth)."""

    API_URL = "https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"

    @property
    def name(self) -> str:
        return "upcitemdb"

    @property
    def supported_types(self) -> set[BarcodeType]:
        return {
            BarcodeType.UPC_A,
            BarcodeType.EAN_13,
            BarcodeType.EAN_8,
            BarcodeType.UPC_E,
            BarcodeType.ISBN_13,
        }

    def lookup(self, value: str) -> LookupResult | None:
        """Query UPCitemdb for a barcode."""
        url = self.API_URL.format(barcode=value)
        request = Request(url, headers={"User-Agent": "barcode-validator/0.1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
        except (OSError, json.JSONDecodeError):
            return None

        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        return LookupResult(
            found=True,
            product_name=item.get("title") or None,
            brand=item.get("brand") or None,
            category=item.get("category") or None,
            source=self.name,
        )
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_lookup.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/lookup.py tests/test_lookup.py
git commit -m "feat(epic-006): implement UPCitemdbProvider"
```

---

### Task 5: Add default service factory

**Files:**
- Modify: `src/barcode_validator/lookup.py`
- Modify: `tests/test_lookup.py`

- [ ] **Step 1: Write failing test**

Add to `tests/test_lookup.py`:

```python
from barcode_validator.lookup import create_lookup_service


def test_create_lookup_service_returns_service_with_default_providers():
    service = create_lookup_service()
    assert isinstance(service, LookupService)
    # Should have 2 providers: OpenFoodFacts and UPCitemdb
    assert len(service._providers) == 2
    assert service._providers[0].name == "open_food_facts"
    assert service._providers[1].name == "upcitemdb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_lookup.py::test_create_lookup_service_returns_service_with_default_providers -v`
Expected: FAIL — `ImportError: cannot import name 'create_lookup_service'`

- [ ] **Step 3: Implement factory function**

Add to the bottom of `src/barcode_validator/lookup.py`:

```python
def create_lookup_service() -> LookupService:
    """Create a LookupService with the default built-in providers."""
    return LookupService([
        OpenFoodFactsProvider(),
        UPCitemdbProvider(),
    ])
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_lookup.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/lookup.py tests/test_lookup.py
git commit -m "feat(epic-006): add create_lookup_service factory"
```

---

### Task 6: Integrate lookup into the validation pipeline

**Files:**
- Modify: `src/barcode_validator/validator.py`
- Modify: `src/barcode_validator/__init__.py`
- Modify: `tests/test_validator.py`

- [ ] **Step 1: Write failing test for validator with lookup**

Add to `tests/test_validator.py`:

```python
from barcode_validator.lookup import LookupService, LookupProvider
from barcode_validator.models import BarcodeType, DecodedBarcode, LookupResult


class FakeLookupProvider(LookupProvider):
    @property
    def name(self) -> str:
        return "fake"

    @property
    def supported_types(self) -> set[BarcodeType]:
        return {BarcodeType.UPC_A, BarcodeType.EAN_13}

    def lookup(self, value: str) -> LookupResult | None:
        return LookupResult(
            found=True,
            product_name="Test Product",
            brand="Test Brand",
            category="Food",
            source="fake",
        )


def test_validate_barcodes_with_lookup():
    decoded = [
        DecodedBarcode(value="0850031591271", symbology="EAN13", page=1),
    ]
    service = LookupService([FakeLookupProvider()])
    result = validate_barcodes(decoded, "test.pdf", lookup_service=service)
    assert result.barcodes[0].lookup is not None
    assert result.barcodes[0].lookup.found is True
    assert result.barcodes[0].lookup.product_name == "Test Product"


def test_validate_barcodes_without_lookup():
    decoded = [
        DecodedBarcode(value="0850031591271", symbology="EAN13", page=1),
    ]
    result = validate_barcodes(decoded, "test.pdf")
    assert result.barcodes[0].lookup is None
```

Make sure to import `validate_barcodes` at the top of the file if not already imported.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_validator.py::test_validate_barcodes_with_lookup -v`
Expected: FAIL — `TypeError: validate_barcodes() got an unexpected keyword argument 'lookup_service'`

- [ ] **Step 3: Update `validate_barcodes()` to accept and use `lookup_service`**

In `src/barcode_validator/validator.py`, update the function signature and body:

```python
"""Orchestrator — classify, validate, and compare decoded barcodes."""

from __future__ import annotations

from typing import TYPE_CHECKING

from barcode_validator.checkdigit import validate_checkdigit
from barcode_validator.classifier import classify
from barcode_validator.comparator import match_expected
from barcode_validator.formatvalidator import validate_format
from barcode_validator.models import BarcodeResult, DecodedBarcode, ValidationResult

if TYPE_CHECKING:
    from barcode_validator.lookup import LookupService


def validate_barcodes(
    decoded: list[DecodedBarcode],
    file_path: str,
    expected_barcodes: list[str] | None = None,
    lookup_service: LookupService | None = None,
) -> ValidationResult:
    """Classify, validate, and optionally compare decoded barcodes.

    Args:
        decoded: Raw decoded barcodes from the decoder.
        file_path: Original file path (for the output).
        expected_barcodes: Expected values for comparison mode. None = decode-only.
        lookup_service: Optional lookup service for public DB queries.
    """
    mode = "comparison" if expected_barcodes is not None else "decode"

    matches_dict: dict[str, bool] = {}
    not_found: list[str] = []
    if expected_barcodes is not None:
        matches_dict, not_found = match_expected(
            [b.value for b in decoded], expected_barcodes
        )

    results: list[BarcodeResult] = []
    for barcode in decoded:
        barcode_type = classify(barcode)
        valid_format = validate_format(barcode.value, barcode_type)
        valid_checkdigit = validate_checkdigit(barcode.value, barcode_type)
        matches_expected = (
            matches_dict.get(barcode.value, False)
            if expected_barcodes is not None
            else None
        )
        lookup_result = None
        if lookup_service is not None:
            lookup_result = lookup_service.lookup(barcode.value, barcode_type)
        results.append(
            BarcodeResult(
                value=barcode.value,
                barcode_type=barcode_type,
                symbology=barcode.symbology,
                page=barcode.page,
                valid_format=valid_format,
                valid_checkdigit=valid_checkdigit,
                matches_expected=matches_expected,
                lookup=lookup_result,
            )
        )

    if mode == "decode":
        passed = bool(results) and all(
            b.valid_format and b.valid_checkdigit is not False for b in results
        )
    else:
        passed = len(not_found) == 0 and all(
            b.matches_expected for b in results if b.matches_expected is not None
        )

    count = len(results)
    verdict = "All validations passed." if passed else "Validation failed."
    summary = f"{count} barcode(s) found. {verdict}"

    return ValidationResult(
        file=file_path,
        passed=passed,
        mode=mode,
        barcodes=results,
        expected_not_found=not_found,
        summary=summary,
    )
```

- [ ] **Step 4: Update `validate_label()` in `__init__.py`**

In `src/barcode_validator/__init__.py`, update to accept and pass through `lookup_service`:

```python
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import load_images
from barcode_validator.models import BarcodeResult, BarcodeType, DecodedBarcode, LookupResult, ValidationResult
from barcode_validator.validator import validate_barcodes

if TYPE_CHECKING:
    from barcode_validator.lookup import LookupService


def decode_file(file_path: Path) -> list[DecodedBarcode]:
    """Decode all barcodes from a label proof file.

    Accepts PDF, AI, PSD, PNG, JPG, TIFF, BMP.
    Returns a list of DecodedBarcode with value, symbology, and page number.
    """
    pages = load_images(file_path)
    return decode_barcodes(pages)


def validate_label(
    file_path: str | Path,
    expected_barcodes: list[str] | None = None,
    lookup_service: LookupService | None = None,
) -> ValidationResult:
    """Validate barcodes on a label proof file.

    Decode-only mode (no expected): decodes, classifies, validates format/checkdigit.
    Comparison mode (expected provided): additionally compares against expected values.
    Lookup: when lookup_service is provided, queries public barcode databases.
    """
    path = Path(file_path)
    pages = load_images(path)
    decoded = decode_barcodes(pages)
    return validate_barcodes(decoded, str(file_path), expected_barcodes, lookup_service)


__all__ = [
    "decode_file",
    "DecodedBarcode",
    "LookupResult",
    "validate_label",
    "ValidationResult",
    "BarcodeResult",
    "BarcodeType",
]
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_validator.py -v`
Expected: ALL PASS

- [ ] **Step 6: Run full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS — no regressions

- [ ] **Step 7: Commit**

```bash
git add src/barcode_validator/validator.py src/barcode_validator/__init__.py tests/test_validator.py
git commit -m "feat(epic-006): integrate lookup into validation pipeline"
```

---

### Task 7: Add `--no-lookup` CLI flag and wire it up

**Files:**
- Modify: `src/barcode_validator/cli_parser.py`
- Modify: `src/barcode_validator/cli.py`
- Modify: `tests/test_cli_parser.py`
- Modify: `tests/test_cli.py`

- [ ] **Step 1: Write failing test for `--no-lookup` parser flag**

Add to `tests/test_cli_parser.py`:

```python
def test_no_lookup_flag_default():
    args = parse_args(["test.pdf"])
    assert args.no_lookup is False


def test_no_lookup_flag_set():
    args = parse_args(["test.pdf", "--no-lookup"])
    assert args.no_lookup is True
```

Make sure `parse_args` is imported at the top of the file.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_parser.py::test_no_lookup_flag_default -v`
Expected: FAIL — `AttributeError: ... has no attribute 'no_lookup'`

- [ ] **Step 3: Add `--no-lookup` to parser**

In `src/barcode_validator/cli_parser.py`, add after the `--output` argument:

```python
    parser.add_argument(
        "--no-lookup",
        action="store_true",
        default=False,
        help="disable public barcode lookup (offline mode)",
    )
```

Update the docstring on `parse_args`:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments. Returns namespace with: files, expected, json, output, no_lookup."""
```

- [ ] **Step 4: Run parser tests**

Run: `uv run pytest tests/test_cli_parser.py -v`
Expected: ALL PASS

- [ ] **Step 5: Wire lookup into CLI**

In `src/barcode_validator/cli.py`, update imports and the `main()` function:

```python
"""CLI main orchestrator for barcode-validator."""

import sys
from pathlib import Path

from barcode_validator import validate_label
from barcode_validator.cli_parser import parse_args
from barcode_validator.cli_format import format_human, format_json, format_json_array, format_error
from barcode_validator.lookup import create_lookup_service


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=pass, 1=fail, 2=error)."""
    args = parse_args(argv)
    exit_code = 0

    if args.output:
        args.json = True
        output_path = Path(args.output)
        if not output_path.parent.exists():
            print(f"Error: output directory does not exist: {output_path.parent}", file=sys.stderr)
            return 2

    lookup_service = None if args.no_lookup else create_lookup_service()

    results = []
    for file_path in args.files:
        try:
            result = validate_label(file_path, expected_barcodes=args.expected, lookup_service=lookup_service)
            if args.output:
                results.append(result)
            elif args.json:
                print(format_json(result))
            else:
                print(format_human(result), file=sys.stderr)
            if not result.passed:
                exit_code = max(exit_code, 1)
        except (FileNotFoundError, ValueError) as exc:
            print(format_error(file_path, exc), file=sys.stderr)
            exit_code = max(exit_code, 2)
        except Exception as exc:
            print(format_error(file_path, exc), file=sys.stderr)
            exit_code = max(exit_code, 2)

    if args.output:
        try:
            output_path.write_text(format_json_array(results))
        except OSError as exc:
            print(f"Error: cannot write output file: {exc}", file=sys.stderr)
            exit_code = max(exit_code, 2)

    return exit_code
```

- [ ] **Step 6: Update CLI tests for lookup integration**

In `tests/test_cli.py`, check existing tests. They should still pass because lookup will attempt network calls but failures are non-fatal. However, for test isolation, mock the lookup service. Add at the top of the test file:

```python
from unittest.mock import patch
```

Add a `conftest`-level or module-level fixture that patches `create_lookup_service` to return a service with no providers (so no network calls during tests):

```python
@pytest.fixture(autouse=True)
def disable_lookup_in_tests(monkeypatch):
    """Prevent real network calls in CLI tests."""
    from barcode_validator.lookup import LookupService
    monkeypatch.setattr(
        "barcode_validator.cli.create_lookup_service",
        lambda: LookupService([]),
    )
```

- [ ] **Step 7: Run all tests**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 8: Commit**

```bash
git add src/barcode_validator/cli_parser.py src/barcode_validator/cli.py tests/test_cli_parser.py tests/test_cli.py
git commit -m "feat(epic-006): add --no-lookup CLI flag and wire lookup into CLI"
```

---

### Task 8: Add lookup info to human-readable output

**Files:**
- Modify: `src/barcode_validator/cli_format.py`
- Modify: `tests/test_cli_format.py`

- [ ] **Step 1: Write failing test for lookup in human output**

Add to `tests/test_cli_format.py`:

```python
from barcode_validator.models import BarcodeResult, BarcodeType, LookupResult, ValidationResult
from barcode_validator.cli_format import format_human


def test_format_human_with_lookup():
    lookup = LookupResult(
        found=True,
        product_name="Test Product",
        brand="Test Brand",
        category="Food",
        source="open_food_facts",
    )
    bc = BarcodeResult(
        value="0850031591271",
        barcode_type=BarcodeType.EAN_13,
        symbology="EAN13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
        lookup=lookup,
    )
    result = ValidationResult(
        file="test.pdf",
        passed=True,
        mode="decode",
        barcodes=[bc],
        expected_not_found=[],
        summary="1 barcode(s) found. All validations passed.",
    )
    output = format_human(result)
    assert "Test Product" in output
    assert "Test Brand" in output


def test_format_human_with_lookup_not_found():
    lookup = LookupResult(
        found=False,
        product_name=None,
        brand=None,
        category=None,
        source=None,
    )
    bc = BarcodeResult(
        value="0000000000000",
        barcode_type=BarcodeType.EAN_13,
        symbology="EAN13",
        page=1,
        valid_format=True,
        valid_checkdigit=True,
        matches_expected=None,
        lookup=lookup,
    )
    result = ValidationResult(
        file="test.pdf",
        passed=True,
        mode="decode",
        barcodes=[bc],
        expected_not_found=[],
        summary="1 barcode(s) found. All validations passed.",
    )
    output = format_human(result)
    assert "not found" in output.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_format.py::test_format_human_with_lookup -v`
Expected: FAIL — "Test Product" not in output

- [ ] **Step 3: Update `format_human()` to include lookup info**

In `src/barcode_validator/cli_format.py`, update the `format_human` function. After the existing detail line for each barcode, add lookup info:

```python
def format_human(result: ValidationResult) -> str:
    """Format a ValidationResult as human-readable text for stderr."""
    lines = [
        f"File: {result.file}",
        f"Mode: {result.mode} | Passed: {'true' if result.passed else 'false'}",
    ]

    if result.barcodes:
        lines.append("Barcodes:")
        for bc in result.barcodes:
            parts = [f"format: {'OK' if bc.valid_format else 'FAIL'}"]
            if bc.valid_checkdigit is not None:
                parts.append(f"checkdigit: {'OK' if bc.valid_checkdigit else 'FAIL'}")
            if bc.matches_expected is not None:
                parts.append(f"match: {'OK' if bc.matches_expected else 'FAIL'}")
            detail = ", ".join(parts)
            lines.append(
                f"  [{bc.page}] {bc.value}  {bc.barcode_type.value}  ({detail})"
            )
            if bc.lookup is not None:
                if bc.lookup.found:
                    lookup_parts = []
                    if bc.lookup.product_name:
                        lookup_parts.append(bc.lookup.product_name)
                    if bc.lookup.brand:
                        lookup_parts.append(f"by {bc.lookup.brand}")
                    lines.append(f"        Lookup: {' '.join(lookup_parts)}")
                else:
                    lines.append("        Lookup: not found in public databases")
    else:
        lines.append("Barcodes: (none)")

    lines.append(f"Summary: {result.summary}")
    return "\n".join(lines)
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_cli_format.py -v`
Expected: ALL PASS

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/cli_format.py tests/test_cli_format.py
git commit -m "feat(epic-006): show lookup info in human-readable CLI output"
```

---

### Task 9: Register `network` pytest marker and add integration tests

**Files:**
- Modify: `pyproject.toml`
- Modify: `tests/test_lookup.py`

- [ ] **Step 1: Register the `network` marker in `pyproject.toml`**

In `pyproject.toml`, add to the `[tool.pytest.ini_options]` section:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["tests"]
markers = [
    "network: tests that require internet access (deselect with '-m not network')",
]
```

- [ ] **Step 2: Add network integration tests**

Add to `tests/test_lookup.py`:

```python
import pytest


@pytest.mark.network
class TestOpenFoodFactsIntegration:
    """Integration tests hitting the real Open Food Facts API."""

    def test_real_lookup_known_ean(self):
        provider = OpenFoodFactsProvider()
        # 0850031591271 is a real EAN-13 from test_docs
        result = provider.lookup("0850031591271")
        # We can't assert exact product data (it may change),
        # but we can verify the response structure
        if result is not None:
            assert result.found is True
            assert result.source == "open_food_facts"

    def test_real_lookup_unknown_barcode(self):
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0000000000000")
        assert result is None


@pytest.mark.network
class TestUPCitemdbIntegration:
    """Integration tests hitting the real UPCitemdb API."""

    def test_real_lookup_known_ean(self):
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        if result is not None:
            assert result.found is True
            assert result.source == "upcitemdb"
```

- [ ] **Step 3: Run unit tests only (skipping network)**

Run: `uv run pytest -v -m "not network"`
Expected: ALL PASS, network tests skipped

- [ ] **Step 4: Run network tests (opt-in verification)**

Run: `uv run pytest -v -m network`
Expected: PASS (requires internet)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/test_lookup.py
git commit -m "feat(epic-006): add network pytest marker and integration tests"
```

---

### Task 10: Update documentation

**Files:**
- Modify: `docs/PRD.md`
- Modify: `SKILL.md`

- [ ] **Step 1: Update PRD to relax offline constraint**

Read `docs/PRD.md` and find the "Fully offline" constraint. Update it to:

> Core decoding and validation engine is fully offline. The optional lookup extension makes network calls to free public APIs (Open Food Facts, UPCitemdb) to retrieve product information. Use `--no-lookup` to disable.

Also update the "Out of Scope" section — remove "Product data lookup" from out-of-scope since it's now implemented.

- [ ] **Step 2: Update SKILL.md**

Read `SKILL.md` and add documentation for the `--no-lookup` flag. Update usage examples to show lookup output. Add a note that lookup is on by default and can be disabled for offline use.

- [ ] **Step 3: Run full test suite one final time**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 4: Commit**

```bash
git add docs/PRD.md SKILL.md
git commit -m "docs(epic-006): update PRD and SKILL.md for lookup extension"
```

---

### Task 11: Final verification and epic completion

- [ ] **Step 1: End-to-end manual test with real file**

Run: `uv run barcode-validator "test_docs/(proof)(BL6)(540841).pdf" --json`

Verify:
- JSON output contains `"lookup"` field for the EAN-13 barcode
- If network is available, lookup should show product info or `found: false`

- [ ] **Step 2: Test `--no-lookup` flag**

Run: `uv run barcode-validator "test_docs/(proof)(BL6)(540841).pdf" --json --no-lookup`

Verify:
- JSON output has `"lookup": null` for all barcodes

- [ ] **Step 3: Test FNSKU file (no lookup expected)**

Run: `uv run barcode-validator "test_docs/EXCEL PRINTPACK-0480-01 proof.pdf" --json`

Verify:
- FNSKU barcode has `"lookup": null` (not eligible for public DB lookup)

- [ ] **Step 4: Full test suite**

Run: `uv run pytest -v`
Expected: ALL PASS

- [ ] **Step 5: Update roadmap — mark EPIC-006 Complete**

In `docs/roadmap.md`, change EPIC-006 status from `Active` to `Complete`.

- [ ] **Step 6: Final commit**

```bash
git add docs/roadmap.md
git commit -m "chore(epic-006): mark epic complete"
```
