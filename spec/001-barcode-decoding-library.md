# ADR-001: Barcode Decoding Library

## Status

Accepted

## Context

Need Python barcode decoder. Self-contained, no external APIs. Must support Code 128 (FNSKU), UPC-A/E, EAN-13/8. Minimal system deps, actively maintained, accurate on clean proofs.

Full analysis: `docs/research/barcode-reading-libraries.md`

| Library | System Deps | Multi-Barcode | Active | Accuracy |
| ------- | ----------- | ------------- | ------ | -------- |
| pyzbar | zbar C lib | 85% | No | 71.2% |
| zxing-cpp v3.0.0 | None | 23.8% | Yes (Feb 2026) | 65.9% |
| OpenCV barcode | None | N/A | Yes | Limited |
| Dynamsoft | None | Good | Yes | 90.6% (commercial) |

## Decision

**Primary: zxing-cpp v3.0.0. Fallback: pyzbar (optional).**

### zxing-cpp primary because

- Zero system deps — pure pip install
- Active — v3.0.0, Python 3.10-3.14
- Broad formats — Code 128, UPC, EAN, QR, Data Matrix, PDF417
- `read_barcodes()` multi-barcode API
- Fast — 40.2 ms avg

### Not pyzbar primary because

- Inactive — no releases 12+ months, effectively abandoned
- Requires zbar C lib system install

### pyzbar fallback because

- Better multi-barcode (85% vs 23.8%)
- Insurance if zxing-cpp misses

### Accuracy risk (65.9%)

Mitigated: we scan **clean label proofs** (high-res PDFs), not blurry photos. Real accuracy on clean inputs much higher.

## Consequences

- `zxing-cpp` = required dep
- `pyzbar` = optional (via extras)
- If neither decodes → preprocessing retry (ADR-003) before reporting failure
