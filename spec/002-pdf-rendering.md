# ADR-002: PDF Rendering Library Selection

## Status

Accepted

## Context

Label proofs arrive as PDF files. We need to render PDF pages to raster images before barcode detection. Requirements:

- Self-contained (no system dependencies)
- Fast enough for interactive use (< 1 second per page)
- Sufficient image quality for barcode detection (300 DPI equivalent)
- Cross-platform (macOS, Linux, Windows)

Options evaluated (full analysis in `docs/research/pdf-image-extraction-pipeline.md`):

| Library | System Deps | Speed | Self-Contained |
| ------- | ----------- | ----- | -------------- |
| PyMuPDF (fitz) | None | 300+ pages/sec | Yes |
| pypdfium2 | None | 200-250 pages/sec | Yes |
| pdf2image | Poppler | 60-100 pages/sec | No |
| pikepdf | None | N/A | Yes (images only) |

## Decision

**PyMuPDF (`fitz`)**.

### Why

- **Zero system dependencies** — MuPDF engine bundled with pip package
- **Fastest option** — 300+ pages/second, rendering a single label page takes ~3 ms
- **Feature-rich** — can render full pages, clip regions, extract text
- **Cross-platform** — wheels available for macOS, Linux, Windows
- **Proven** — widely used in production PDF processing

### Why not pypdfium2

- Slightly slower (200-250 pps vs 300+)
- Less feature-rich
- Would be an acceptable alternative if PyMuPDF licensing (AGPL for MuPDF) becomes a concern

### Why not pdf2image

- Requires Poppler system library — violates self-contained requirement
- 3-5x slower than PyMuPDF

## Consequences

- `PyMuPDF` is a required dependency
- PDFs are rendered at 2x scale (equivalent to ~144-300 DPI depending on source) for optimal barcode detection
- Single-page memory footprint: ~25 MB per A4 page at 300 DPI RGB — acceptable for label proofs
