# ADR-002: PDF Rendering Library

## Status

Accepted

## Context

Must render PDF pages to raster images for barcode detection. No system deps, < 1s/page, 300 DPI quality, cross-platform.

Full analysis: `docs/research/pdf-image-extraction-pipeline.md`

| Library | System Deps | Speed | Self-Contained |
| ------- | ----------- | ----- | -------------- |
| PyMuPDF (fitz) | None | 300+ pps | Yes |
| pypdfium2 | None | 200-250 pps | Yes |
| pdf2image | Poppler | 60-100 pps | No |
| pikepdf | None | N/A | Yes (images only) |

## Decision

**PyMuPDF (`fitz`).**

### Why

- Zero system deps — MuPDF bundled in pip
- Fastest — 300+ pps, ~3 ms per label page
- Feature-rich — page render, region clip, text extract
- Cross-platform wheels (macOS/Linux/Windows)

### Not pypdfium2

- Slower, less features. Acceptable backup if AGPL licensing concern.

### Not pdf2image

- Requires Poppler system lib. 3-5x slower.

## Consequences

- `PyMuPDF` = required dep
- Render at 2x scale (~144-300 DPI) for barcode detection
- ~25 MB memory per A4 page at 300 DPI RGB — fine for label proofs
