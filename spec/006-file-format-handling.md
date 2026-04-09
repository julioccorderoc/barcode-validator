# ADR-006: File Format Handling

## Status

Accepted

## Context

Label proofs arrive in various formats. Need to convert all to raster images for barcode detection.

## Decision

### Format routing

| Format | Extensions | Path | Library |
| ------ | ---------- | ---- | ------- |
| PDF | `.pdf` | Render pages | PyMuPDF |
| Illustrator | `.ai` | Treat as PDF | PyMuPDF |
| Photoshop | `.psd` | Flattened composite | Pillow |
| Raster | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp` | Open direct | Pillow |

### AI as PDF

AI files with "Create PDF Compatible File" (default) embed full PDF. PyMuPDF opens directly. No extra library. If saved without PDF compat → error: "Re-export with PDF Compatible File enabled." PyMuPDF raises exception on invalid.

### PSD via Pillow

Pillow reads PSD flattened composite natively — merged visual output. Exactly what we need (final printed label). No extra library. Only reads composite, not layers. Fine for our use case.

### Extension-based detection

By extension, not magic bytes. Files from known design workflows, not untrusted sources. Simpler. PyMuPDF/Pillow raise clear errors on content mismatch.

### Routing logic

```text
{.pdf, .ai}                              → PyMuPDF render
{.psd}                                   → Pillow.open() composite
{.png, .jpg, .jpeg, .tiff, .tif, .bmp}  → Pillow.open()
otherwise                                → error: unsupported
```

## Consequences

- No new deps beyond PyMuPDF + Pillow
- AI support = free (same as PDF)
- PSD support = free (Pillow built-in)
- Future formats (SVG) = new processing path
