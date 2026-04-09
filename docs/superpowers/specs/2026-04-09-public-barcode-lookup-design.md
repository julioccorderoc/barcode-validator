# Public Barcode Lookup Extension — Design Spec

> Date: 2026-04-09
> Epic: EPIC-006
> Status: Draft

## Problem

barcode-validator decodes, classifies, and validates barcodes on label proofs, but it only checks format and check digits. It cannot tell the user whether a UPC/EAN/ISBN is actually registered to a real product. Ops team members currently have to manually look up barcodes on websites to verify product association.

## Goal

Add a public barcode lookup feature that queries free, no-auth APIs to retrieve product information for decoded barcodes. This is an informational extension — it enriches the output but does not affect the pass/fail verdict.

## Design Decisions

### Connectivity Model

The core decoding/validation engine remains fully offline. Lookup is a **post-validation extension** that makes network calls. It is enabled by default but can be disabled with `--no-lookup` to restore fully-offline behavior. Network failures are non-fatal.

### Provider Architecture

Pluggable provider system with an abstract base class and a service orchestrator.

```
LookupProvider (ABC)
├── OpenFoodFactsProvider   # built-in, tried first
├── UPCitemdbProvider        # built-in, fallback
└── (future) AmazonProvider  # ASIN/FNSKU placeholder
```

**`LookupProvider` ABC** defines:
- `name: str` — provider identifier (e.g., `"open_food_facts"`)
- `supported_types: set[BarcodeType]` — which barcode types this provider handles
- `lookup(value: str) -> LookupResult | None` — returns result or None if not found

**`LookupService`** orchestrates:
- Maintains an ordered list of providers
- For a given barcode, filters to providers that support its type
- Tries each in order until one returns a result
- Returns `None` if all providers miss or fail

### Barcode Type Routing

| Barcode Type | Providers | Rationale |
|-------------|-----------|-----------|
| UPC_A | OpenFoodFacts, UPCitemdb | Standard product codes with public DB coverage |
| EAN_13 | OpenFoodFacts, UPCitemdb | International product codes |
| EAN_8 | OpenFoodFacts, UPCitemdb | Compact product codes |
| ISBN_13 | UPCitemdb | Book ISBNs — UPCitemdb has better ISBN coverage |
| UPC_E | UPCitemdb | Compact UPC — less common in food DBs |
| FNSKU | *(none — future)* | Amazon-internal, needs Amazon lookup |
| ASIN | *(none — future)* | Amazon-internal, needs Amazon lookup |
| CODE128 | *(none)* | Generic, no public registry |
| CODE39 | *(none)* | Generic, no public registry |

### Built-in Providers

**Open Food Facts** (default, tried first):
- API: `GET https://world.openfoodfacts.net/api/v2/product/{barcode}`
- Auth: None required
- Rate limit: None
- Coverage: 4M+ food products, UPC/EAN
- Returns: product_name, brands, categories

**UPCitemdb** (fallback):
- API: `GET https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}`
- Auth: None for free tier
- Rate limit: 100 requests/day
- Coverage: UPC/EAN/ISBN/GTIN, all product categories
- Returns: title, brand, category

## Data Model

### New dataclass: `LookupResult`

```python
@dataclass(frozen=True)
class LookupResult:
    found: bool
    product_name: str | None
    brand: str | None
    category: str | None
    source: str | None  # provider name
```

### Extended `BarcodeResult`

Add optional field:

```python
@dataclass(frozen=True)
class BarcodeResult:
    # ... existing fields ...
    lookup: LookupResult | None  # None when disabled or not eligible
```

### JSON Output Extension

Each barcode object in the output gains a `lookup` field:

```json
{
  "value": "012345678901",
  "type": "UPC_A",
  "symbology": "EAN-13",
  "page": 1,
  "valid_format": true,
  "valid_checkdigit": true,
  "matches_expected": null,
  "lookup": {
    "found": true,
    "product_name": "Example Product",
    "brand": "Example Brand",
    "category": "Food",
    "source": "open_food_facts"
  }
}
```

States:
- **Lookup disabled** (`--no-lookup`) or **non-eligible type**: `"lookup": null`
- **Looked up, found**: `"lookup": {"found": true, "product_name": "...", ...}`
- **Looked up, not found**: `"lookup": {"found": false, "product_name": null, "brand": null, "category": null, "source": null}`
- **Network error**: `"lookup": null` + stderr warning

## CLI Changes

### New flag: `--no-lookup`

```
--no-lookup    Disable public barcode lookup (offline mode)
```

Lookup is ON by default. `--no-lookup` disables all network calls.

### Behavior

- Lookup runs **after** validation, **before** JSON output
- Network errors are **non-fatal** — stderr warning, `lookup: null`, exit code unaffected
- Lookup does **not** affect `passed` verdict — purely informational
- Human stderr output includes lookup results when found

## Pipeline Integration

```
File → decode → classify → validate → compare expected
  → [lookup enabled?] → query providers per barcode type
  → build ValidationResult (with lookup fields)
  → JSON output
```

## Module Structure

Single new file: `src/barcode_validator/lookup.py`

Contains:
- `LookupResult` dataclass (or add to `models.py`)
- `LookupProvider` ABC
- `OpenFoodFactsProvider`
- `UPCitemdbProvider`
- `LookupService`

HTTP calls use `urllib.request` (stdlib) to avoid adding a dependency like `requests` or `httpx`.

## Testing Strategy

### Unit tests (mocked HTTP)

- Provider parses API response correctly → `LookupResult` with expected fields
- Provider handles 404/not-found → returns `None`
- Provider handles network error → returns `None`, no exception
- Service tries providers in order, stops on first hit
- Service returns `None` when all providers miss
- Non-eligible barcode types → lookup skipped

### Integration tests (real network, opt-in)

Marked with `@pytest.mark.network` and skipped by default:

```bash
uv run pytest -m network  # opt-in to run network tests
```

- Real UPC lookup against Open Food Facts → product info returned
- Real lookup against UPCitemdb → product info returned

### Existing tests

All existing tests must continue to pass. Lookup is `None` in existing test fixtures.

## Documentation Updates

- **PRD** (`docs/PRD.md`): Relax offline constraint — "Core engine is offline. Optional lookup extension makes network calls to free public APIs."
- **SKILL.md**: Document `--no-lookup` flag, update examples
- **CLAUDE.md**: Add lookup module to pipeline description if needed

## Out of Scope

- Amazon ASIN/FNSKU lookup (future epic — `amazon.com/dp/<code>`)
- Local caching / offline database
- Paid API tiers or API key management
- Lookup affecting pass/fail verdict

## Risks

- **API availability**: Free services may go down or change. Mitigation: non-fatal errors, pluggable providers make swapping easy.
- **UPCitemdb rate limit**: 100/day on free tier. Mitigation: Open Food Facts is primary (no limit); UPCitemdb is fallback.
- **Coverage gaps**: No single DB covers all products. Mitigation: two providers with different strengths; `found: false` is a valid result.

## Sources

- [Open Food Facts API](https://world.openfoodfacts.org/data)
- [Open Food Facts API Tutorial](https://openfoodfacts.github.io/openfoodfacts-server/api/tutorial-off-api/)
- [UPCitemdb API](https://devs.upcitemdb.com/)
- [UPCitemdb Free Tier](https://www.upcitemdb.com/api/)
