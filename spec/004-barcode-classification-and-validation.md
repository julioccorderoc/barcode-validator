# ADR-004: Barcode Classification and Validation Logic

## Status

Accepted

## Context

Once a barcode is decoded, we need to:

1. Classify what type of barcode it is (FNSKU, UPC, EAN, ISBN, ASIN, etc.)
2. Validate its integrity (check digit, format)
3. Compare it against an expected value

All validation must be self-contained — no external API calls or database lookups.

## Decision

### Classification: pattern-matching on decoded text

Apply rules in priority order (most specific first):

```text
1. Starts with "X00" + 7 alphanumeric chars → FNSKU
2. 13 digits starting with 978/979 → ISBN-13
3. 12 digits → UPC-A
4. 13 digits → EAN-13
5. 8 digits → EAN-8 or UPC-E (disambiguate by symbology if available)
6. Starts with "B0" + 8 alphanumeric, length=10 → ASIN
7. Alphanumeric in Code 128 symbology → Generic Code 128
8. Otherwise → Unknown (report raw value and symbology)
```

### Validation: deterministic algorithms

| Check | Algorithm | Applies To |
| ----- | --------- | ---------- |
| Check digit | MOD 10 (GTIN algorithm) | UPC-A, UPC-E, EAN-13, EAN-8, ISBN-13 |
| Format | Regex pattern match | All types |
| Value match | Exact string comparison | All types (when expected value provided) |

### Why no external lookups

- Self-contained requirement from PRD
- Check digit + format validation catches the errors that matter for label proofs (wrong barcode printed, transposition errors, truncated values)
- Product data lookup (is this UPC registered to this product?) is a nice-to-have but not needed for proof validation — the user provides the expected value

### Why deterministic only

- Check digit algorithms detect 100% of single-digit errors and ~90% of transposition errors
- For label proofs, the main failure modes are: wrong barcode value, unreadable barcode, or missing barcode — all caught by decode + compare
- No ML/heuristic validation needed

## Consequences

- Classification and validation are pure Python with no dependencies
- Adding new barcode types requires adding a regex pattern and optional check digit algorithm
- External database lookups can be added later as an optional enhancement without changing core architecture
