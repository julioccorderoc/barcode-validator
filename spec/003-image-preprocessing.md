# ADR-003: Image Preprocessing Strategy

## Status

Accepted

## Context

Barcode decoders work best on clean, high-contrast images. Label proofs are already clean but preprocessing handles edge cases (rendering artifacts, slight noise).

## Decision

**OpenCV lightweight pipeline, applied only when needed.**

### Pipeline

```text
Raw image → zxing-cpp decode
    ↓ (no barcodes found)
Grayscale → Gaussian blur (5x5) → Otsu threshold → retry decode
    ↓ (still none)
Report: no barcodes detected
```

### Why this approach

- **Raw first** — proofs are clean, preprocessing may not be needed
- **Otsu threshold** — auto-determines optimal binary threshold, no manual tuning
- **Gaussian blur** — reduces minor noise
- **No rotation correction v1** — proofs from design software, not camera photos

### Why OpenCV

- `opencv-python` sufficient (not `-contrib`)
- Only uses `cvtColor`, `GaussianBlur`, `threshold`

## Consequences

- `opencv-python` = required dep (pulls `numpy`)
- Preprocessing adds ~5 ms when triggered
- Rotation correction = future enhancement if needed
