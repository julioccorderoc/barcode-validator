# Barcode Types & Validation Logic

> Research 2026-04-09. E-commerce/Amazon FBA formats.

---

## UPC (Universal Product Code)

**UPC-A:** 12 digits (6 manufacturer + 5 product + 1 check). Regex: `^\d{12}$`
**UPC-E:** 8 digits (compressed). Regex: `^\d{8}$`

**Check digit (MOD 10):**

1. Odd positions x3, even x1 (from right)
2. Sum all
3. Check = (10 - sum%10) % 10

Example `036000241457`: odd (0+6+0+2+1+5)x3=42, even (3+0+0+4+4)=11, total=53, check=7

---

## EAN

**EAN-13:** 13 digits. Regex: `^\d{13}$`
**EAN-8:** 8 digits. Regex: `^\d{8}$`

Check digit: same MOD 10 as UPC.

---

## FNSKU

- Prefix `X00` + 7 alphanum (e.g., `X001ABC123`)
- Code 128 symbology. Seller-specific.
- Regex: `^X00[A-Z0-9]{7}$`
- Label: 1"x2.625" min, 300 DPI, black on white
- **Jan 2026:** Amazon no longer applies labels — sellers must label before sending.

---

## ASIN

- 10 alphanum: `B0` + 8 chars (products) or 10-digit ISBN (books)
- Not inherently a barcode — Amazon internal ID
- Regex: `^(B[\dA-Z]{9}|\d{9}[\dX])$`

---

## ISBN

**ISBN-13:** 13 digits, 978/979 prefix. Specialized EAN-13. MOD 10 check.
**ISBN-10:** 10 digits. Weights 10-2, mod 11. Check can be X (=10).

---

## Code 128 & Code 39

**Code 128:** High-density, full ASCII, mandatory check digit. Used by carriers, FNSKU, GS1-128.
**Code 39:** 43 chars standard, no mandatory check digit. Military, libraries, legacy. Longer bars than 128.

---

## Validation

### Check Digit (MOD 10)

Applies: UPC, EAN, GTIN, ISBN-13. Catches 100% single-digit errors, ~90% transpositions.

### Format Regex

| Type | Pattern |
| ---- | ------- |
| UPC-A | `^\d{12}$` |
| EAN-13 | `^\d{13}$` |
| EAN-8 | `^\d{8}$` |
| FNSKU | `^X00[A-Z0-9]{7}$` |
| ASIN | `^(B[\dA-Z]{9}\|\d{9}[\dX])$` |
| ISBN-13 | `^97[89]\d{10}$` |

### Auto-Detection Priority

```text
^\d{12}$ → UPC-A
^\d{13}$ + 978/979 → ISBN-13
^\d{13}$ → EAN-13
^\d{8}$ → EAN-8
X00... → FNSKU
B0 + len=10 → ASIN
Code 128 alphanum → Generic Code 128
Otherwise → Unknown
```

### Free Lookup DBs (no API key)

| Service | Coverage |
| ------- | -------- |
| CheckBarcode.com | EAN/UPC/GTIN |
| EAN-Search.org | 1.09B+ products |
| BarcodeFinder | UPC/EAN/ISBN |
| BarcodeLookup | UPC/EAN/ISBN + pricing |

No single global master DB. Coverage varies.

### Amazon Scraping

Feasible but not recommended. Anti-bot measures, ToS restrictions. Better for discovery than real-time validation.

---

## Sources

- [GS1 Check Digit Calculator](https://www.gs1us.org/tools/check-digit-calculator)
- [FNSKU Guide - AmazonPrep](https://amzprep.com/fnsku/)
- [Code 128 vs 39 - Dynamsoft](https://www.dynamsoft.com/blog/insights/code-39-vs-code-128/)
- [Amazon FBA Barcode Requirements](https://sellercentral.amazon.com/gp/help/external/G201100910)
