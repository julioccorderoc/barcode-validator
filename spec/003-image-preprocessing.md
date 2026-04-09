# ADR-003: Image Preprocessing Strategy

## Status

Accepted

## Context

Barcode decoders work best on clean, high-contrast images. While our label proofs are already clean PDFs, preprocessing can improve detection reliability and handle edge cases (slight rotation, noise from PDF rendering artifacts).

## Decision

**Use OpenCV for a lightweight preprocessing pipeline**, applied only when needed.

### Pipeline

```text
Original image → zxing-cpp decode attempt
    ↓ (if no barcodes found)
Grayscale → Gaussian blur (5x5) → Otsu threshold → retry decode
    ↓ (if still no barcodes found)
Report: no barcodes detected
```

### Why this approach

- **Try raw image first** — label proofs are clean; preprocessing may not be needed and adds latency
- **Otsu's thresholding** — automatically determines optimal binary threshold without manual tuning
- **Gaussian blur** — reduces minor noise that could interfere with bar detection
- **No rotation correction in v1** — label proofs come from design software, not camera photos; rotation is unlikely

### Why OpenCV

- Already a transitive dependency of image processing workflows
- `opencv-python` (not `opencv-contrib-python`) is sufficient — we don't need the `BarcodeDetector` module since we use zxing-cpp for decoding
- Lightweight: only used for `cvtColor`, `GaussianBlur`, `threshold`

## Consequences

- `opencv-python` is a required dependency (pulls in `numpy`)
- Preprocessing adds ~5 ms when triggered — negligible
- If future use cases involve rotated/skewed barcodes (e.g., photos of physical labels), add rotation correction as a separate enhancement
