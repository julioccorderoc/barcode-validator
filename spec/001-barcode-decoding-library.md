# ADR-001: Barcode Decoding Library Selection

## Status

Accepted

## Context

We need a Python library to decode barcodes from images extracted from label proofs. Requirements:

- Self-contained (no external APIs)
- Support Code 128 (FNSKU), UPC-A/E, EAN-13/8 at minimum
- Minimal system dependencies
- Actively maintained
- Accurate on clean, high-resolution label proofs

Options evaluated (full analysis in `docs/research/barcode-reading-libraries.md`):

| Library | System Deps | Multi-Barcode | Active | Accuracy (real-world) |
| ------- | ----------- | ------------- | ------ | --------------------- |
| pyzbar | zbar C lib | 85% | No (inactive) | 71.2% |
| zxing-cpp v3.0.0 | None | 23.8% (improved API) | Yes (Feb 2026) | 65.9% |
| OpenCV barcode | None | N/A | Yes | Limited formats |
| Dynamsoft | None | Good | Yes | 90.6% (commercial) |

## Decision

**Primary: zxing-cpp v3.0.0** with **pyzbar as optional fallback**.

### Why zxing-cpp as primary

- **Zero system dependencies** — pure pip install, truly self-contained
- **Actively maintained** — v3.0.0 released Feb 2026, supports Python 3.10-3.14
- **Broad format support** — Code 128, UPC, EAN, QR, Data Matrix, PDF417, and more
- **Multi-barcode API** — `read_barcodes()` now available (though accuracy lags pyzbar)
- **Fast** — 40.2 ms average detection time

### Why not pyzbar as primary

- **Inactive project** — no releases in 12+ months, no PR activity, only 808 GitHub stars
- **Requires system dependency** — zbar C library must be installed separately on macOS/Linux
- Underlying zbar C library is stable but Python wrapper is effectively abandoned

### Why pyzbar as fallback

- Better multi-barcode accuracy (85% vs 23.8%) if multiple barcodes per label become common
- Can be enabled when zbar system lib is available
- Acts as insurance if zxing-cpp misses a barcode

### Risk: zxing-cpp accuracy on real-world images (65.9%)

Mitigated by our use case: we scan **clean label proofs** (high-res PDFs), not blurry photos. Expected accuracy on clean inputs is significantly higher than the 65.9% benchmark measured on diverse real-world images.

## Consequences

- `zxing-cpp` is a required dependency
- `pyzbar` is an optional dependency (installed via extras: `pip install barcode-validator[pyzbar]`)
- If neither library decodes a barcode, preprocessing (ADR-003) is attempted before reporting failure
