# ERRORS.md

> Known bugs and error patterns. Agents update when found/fixed.

## Open

### Decoder fails to extract barcodes from 4 test_docs files — 2026-04-09

Barcodes confirmed present by manual inspection but `validate_label()` returns empty `barcodes[]`.

| File | Expected | Symbology |
|------|----------|-----------|
| `(proof)(BL6)(540837).pdf` | `0850031591264` (EAN-13) | EAN13 |
| `EXCEL PRINTPACK-0480-01 proof.pdf` | `X0032C5SUL` (FNSKU) | Code128 |
| `EXCEL PRINTPACK-0480-04 proof.pdf` | `X002K7DQFD` (FNSKU) | Code128 |
| `(label_artwork)(...)(Level_Off).ai` | `X004781QUF` (FNSKU) | Code128 |

**Repro:** `uv run python -c "from barcode_validator import validate_label; print(validate_label('test_docs/(proof)(BL6)(540837).pdf').barcodes)"`

**Notes:**
- The `.ai` file's barcode decodes fine from the `.jpg` version of the same artwork, suggesting a rendering/resolution issue with PyMuPDF on this file.
- The EXCEL PRINTPACK PDFs and 540837 PDF may need preprocessing tuning or higher render scale.
- Tests marked `xfail` in `tests/test_integration.py` (`_decode_failures` set). Remove as fixed.

## Resolved

<!-- ### Short description / Date fixed / Commit hash / Resolution -->
