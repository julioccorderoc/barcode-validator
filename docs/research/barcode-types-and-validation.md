# Barcode Types & Validation Logic

> Research conducted 2026-04-09. Focus: e-commerce/Amazon FBA barcode formats.

---

## 1. UPC (Universal Product Code)

**UPC-A:** 12 digits total

- First 6: Manufacturer ID (assigned by GS1)
- Next 5: Product ID
- Last 1: Check digit

**UPC-E:** Compressed 6-digit format (8 digits total with parity + check digit)

**Check Digit Algorithm (MOD 10):**

1. Starting from rightmost position, multiply odd-position digits by 3, even by 1
2. Sum all products
3. Check digit = (10 - (sum mod 10)) mod 10

**Example:** UPC-A `036000241457`

- Odd positions: (0+6+0+2+1+5) × 3 = 42
- Even positions: (3+0+0+4+4) = 11
- Total: 53 → Check digit: 10 - (53 mod 10) = 7 ✓

**Regex:** `^\d{12}$`

---

## 2. EAN (European Article Number)

**EAN-13:** 13 digits (12 data + 1 check digit)
**EAN-8:** 8 digits (7 data + 1 check digit) — for small packages

**Check digit:** Same MOD 10 algorithm as UPC (alternating weights 1 and 3).

**Regex:** `^\d{13}$` (EAN-13), `^\d{8}$` (EAN-8)

---

## 3. FNSKU (Fulfillment Network Stock Keeping Unit)

**Format:**

- Always starts with `X00` prefix
- Alphanumeric, typically 10 characters (e.g., `X001ABC123`)
- Encoded as **Code 128** barcode symbology
- Seller-specific (same product, different sellers = different FNSKUs)

**How to identify:** `X00` prefix distinguishes FNSKU from UPC/EAN (numeric-only).

**Two variants:**

- `X0...` — Amazon Barcode
- `B0...` — sometimes used for manufacturer variants

**Regex:** `^X00[A-Z0-9]{7}$`

**Label specs:**

- Size: 1" × 2⅝" minimum
- Resolution: 300 DPI+
- Black ink on white, non-reflective
- Must remain scannable 24 months
- ¼" clearance from edges

**Recent change (Jan 2026):** Amazon no longer applies FNSKU labels — all US FBA sellers must label before sending to fulfillment centers.

---

## 4. ASIN (Amazon Standard Identification Number)

**Format:** 10 alphanumeric characters

- `B0` + 8 alphanumeric (most products): e.g., `B0ABC1XYZ2`
- 10-digit ISBN (books only)

**Not inherently a barcode** — Amazon's internal catalog ID. For books, ASIN = ISBN.

**Regex:** `^(B[\dA-Z]{9}|\d{9}[\dX])$`

---

## 5. ISBN (International Standard Book Number)

**ISBN-13:** 13 digits with Bookland prefix (978 or 979). Technically a specialized EAN-13.
**ISBN-10:** 10 digits (older format).

**Check digit:**

- ISBN-13: Same MOD 10 as EAN-13
- ISBN-10: Sum of (first 9 digits × weights 10→2), mod 11. Check digit can be 0-9 or `X` (=10).

---

## 6. Code 128 & Code 39

**Code 128:**

- High-density 1D barcode, full ASCII 128 character set
- Mandatory check digit
- Used by: shipping carriers (UPS, FedEx, USPS), FNSKU, GS1-128, logistics
- Preferred for modern systems

**Code 39:**

- 43 characters standard (extended: full ASCII via combinations)
- No mandatory check digit
- Used by: military (LOGMARS), libraries, legacy systems
- Produces longer barcodes than Code 128

---

## 7. Validation Approaches

### A. Check Digit Validation (MOD 10)

Applies to: UPC, EAN, GTIN, ISBN-13, ISSN, ISMN, SSCC

Detects: 100% of single-digit errors, ~90% of transposition errors.

### B. Format Validation (Regex)

| Type | Pattern | Notes |
|------|---------|-------|
| UPC-A | `^\d{12}$` | 12 numeric digits |
| EAN-13 | `^\d{13}$` | 13 numeric digits |
| EAN-8 | `^\d{8}$` | 8 numeric digits |
| FNSKU | `^X00[A-Z0-9]{7}$` | X00 + 7 alphanumeric |
| ASIN | `^(B[\dA-Z]{9}\|\d{9}[\dX])$` | 10 chars |
| ISBN-13 | `^97[89]\d{10}$` | Starts with 978/979 |

### C. Barcode Type Auto-Detection Logic

```text
IF decoded text matches ^\d{12}$ → UPC-A (validate check digit)
IF decoded text matches ^\d{13}$ AND starts with 978/979 → ISBN-13
IF decoded text matches ^\d{13}$ → EAN-13 (validate check digit)
IF decoded text matches ^\d{8}$ → EAN-8 (validate check digit)
IF decoded text starts with X00 → FNSKU
IF decoded text starts with B0 AND length=10 → likely ASIN
IF barcode symbology is CODE128 with alphanumeric → check FNSKU/ASIN patterns
```

### D. Free Barcode Lookup Databases (No API Key Required)

| Service | Coverage | Notes |
|---------|----------|-------|
| [CheckBarcode.com](https://www.checkbarcode.com/en) | EAN/UPC/GTIN | Free validation, GS1 prefix lookup |
| [EAN-Search.org](https://www.ean-search.org/) | 1.09B+ products | Free lookup by EAN/GTIN/UPC/ISBN |
| [BarcodeFinder](https://www.barcodefinder.info/) | UPC/EAN/ISBN | No account required |
| [BarcodeLookup](https://www.barcodelookup.com/) | UPC/EAN/ISBN | Product data + pricing |

**Caveat:** No single free global master database exists. Coverage varies.

### E. Amazon Product Page Scraping

- Technically feasible (ASIN in `/dp/B0ABC1XYZ2` URL, `data-asin` attribute)
- **Challenges:** IP blocking, CAPTCHA, dynamic content, rate limiting
- **Legal:** Amazon ToS restricts automated collection; hiQ v. LinkedIn (2022) allows public data scraping
- **Verdict:** Better for discovery than real-time validation. Not recommended for a self-contained skill.

---

## Sources

- [GS1 Check Digit Calculator](https://www.gs1us.org/tools/check-digit-calculator)
- [Medium: UPC/EAN Check Digit Implementation](https://medium.com/@michael.harges/implementing-the-upc-ean-check-digit-algorithm-in-c-e99c26a540c8)
- [FNSKU Complete Guide - AmazonPrep](https://amzprep.com/fnsku/)
- [FNSKU vs UPC - BarCodesTalk](https://www.barcodestalk.com/learn-about-barcodes/resources/fnsku-vs-upc)
- [Code 128 vs Code 39 - Dynamsoft](https://www.dynamsoft.com/blog/insights/code-39-vs-code-128/)
- [Amazon Seller Central FBA Barcode Requirements](https://sellercentral.amazon.com/gp/help/external/G201100910)
