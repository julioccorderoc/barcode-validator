# ADR-006: File Format Handling

## Status

Accepted

## Context

Label proofs arrive in various formats depending on the design tool used. We need to convert all supported formats into a raster image for barcode detection.

## Decision

### Supported formats and their processing paths

| Format | Extensions | Processing Path | Library |
| ------ | ---------- | --------------- | ------- |
| PDF | `.pdf` | Render pages to images | PyMuPDF |
| Adobe Illustrator | `.ai` | Treat as PDF (render pages) | PyMuPDF |
| Photoshop | `.psd` | Read flattened composite | Pillow |
| Raster images | `.png`, `.jpg`, `.jpeg`, `.tiff`, `.tif`, `.bmp` | Open directly | Pillow |

### Adobe Illustrator (`.ai`) as PDF

AI files saved with "Create PDF Compatible File" (the default in Illustrator) embed a full PDF representation. PyMuPDF can open and render these directly as PDFs.

- **No additional library needed** — same path as PDF
- **Risk:** If an AI file was saved without PDF compatibility, it cannot be opened. In that case, return a clear error: "AI file is not PDF-compatible. Re-export with 'Create PDF Compatible File' enabled."
- Detection: PyMuPDF will raise an exception on open if the file isn't a valid PDF

### Photoshop (`.psd`) via Pillow

Pillow natively reads PSD files and returns the flattened composite image — the merged visual output of all layers. This is exactly what we need for barcode scanning.

- **No additional library needed** — Pillow handles it
- **Limitation:** Only reads the flattened composite, not individual layers. This is fine for our use case — we scan what the final printed label will look like.
- If the PSD has no flattened composite (rare), Pillow may return only the first layer. This is acceptable for v1.

### Format detection

Detect format by file extension, not by magic bytes. Rationale:

- Input files come from known design workflows, not untrusted sources
- Extension-based routing is simpler and sufficient
- PyMuPDF and Pillow will raise clear errors if the file content doesn't match

### Routing logic

```text
extension in {.pdf, .ai}  → PyMuPDF render pipeline
extension in {.psd}        → Pillow.open() → get composite image
extension in {.png, .jpg, .jpeg, .tiff, .tif, .bmp} → Pillow.open()
otherwise                  → error: unsupported format
```

## Consequences

- No new dependencies beyond PyMuPDF and Pillow (already in the stack)
- AI support is essentially free (same code path as PDF)
- PSD support is essentially free (Pillow built-in)
- Adding future formats (e.g., SVG) would require a new processing path
