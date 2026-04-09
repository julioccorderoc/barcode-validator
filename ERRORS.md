# ERRORS.md

> Known bugs and error patterns. Agents update when found/fixed.

## Open

<!-- None -->

## Resolved

### Decoder fails to extract barcodes from 4 test_docs files — 2026-04-09 / Fixed 2026-04-09

**Root cause:** PyMuPDF 2x render scale produced images too small for zxing-cpp to decode barcodes on these files. The .ai file rendered at 1099x415 vs the .jpg source at 2290x866.

**Fix:** Bumped render scale from 2x to 3x in `loader.py`. All 4 files now decode correctly. Tests updated — xfail markers removed, assertions upgraded to verify extracted values.
