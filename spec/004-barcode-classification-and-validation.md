# ADR-004: Barcode Classification and Validation

## Status

Accepted

## Context

After decode: classify type, validate integrity, compare expected. All self-contained — no APIs or DB lookups.

## Decision

### Classification: priority-ordered pattern matching

```text
1. "X00" + 7 alphanum → FNSKU
2. 13 digits, 978/979 prefix → ISBN-13
3. 12 digits → UPC-A
4. 13 digits → EAN-13
5. 8 digits → EAN-8 or UPC-E (disambiguate by symbology)
6. "B0" + 8 alphanum, len=10 → ASIN
7. Alphanum in Code 128 symbology → Generic Code 128
8. Otherwise → Unknown
```

### Validation: deterministic algorithms

| Check | Algorithm | Applies To |
| ----- | --------- | ---------- |
| Check digit | MOD 10 (GTIN) | UPC-A, UPC-E, EAN-13, EAN-8, ISBN-13 |
| Format | Regex | All types |
| Value match | Exact string compare | All (when expected provided) |

### No external lookups

- Self-contained requirement. Check digit + format catches what matters for proofs (wrong barcode, transposition, truncation). User provides expected value.

### Deterministic only

- Check digit catches 100% single-digit errors, ~90% transpositions. Main failures: wrong value, unreadable, missing — all caught by decode + compare.

## Consequences

- Pure Python, no deps
- New barcode type = new regex + optional check digit algo
- External lookups can bolt on later without changing core
