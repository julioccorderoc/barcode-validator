# EPIC-001: Core Decoding Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Accept label proof files (PDF, AI, PSD, PNG, JPG, TIFF, BMP) and decode all barcodes present, producing raw decoded values and symbology metadata.

**Architecture:** Extension-based routing sends files to the right loader (PyMuPDF for PDF/AI, Pillow for PSD/raster). Each loader produces a list of PIL Images with page numbers. Images are fed to zxing-cpp for decoding, with an OpenCV preprocessing retry if the first pass finds nothing. Output is a flat list of `DecodedBarcode` dataclasses.

**Tech Stack:** PyMuPDF, zxing-cpp, OpenCV, Pillow, pytest

---

## File Structure

| File | Responsibility |
| ---- | -------------- |
| `src/barcode_validator/__init__.py` | Package root. Exports `decode_file` and `DecodedBarcode`. |
| `src/barcode_validator/models.py` | `DecodedBarcode` dataclass (value, symbology, page). |
| `src/barcode_validator/loader.py` | File format routing + image loading. Returns `list[PageImage]`. |
| `src/barcode_validator/decoder.py` | Barcode decoding: zxing-cpp primary, preprocessing retry, optional pyzbar fallback. |
| `src/barcode_validator/preprocessing.py` | OpenCV preprocessing pipeline (grayscale → blur → threshold). |
| `tests/__init__.py` | Test package. |
| `tests/conftest.py` | Shared fixtures (test_docs paths, sample images). |
| `tests/test_models.py` | Tests for DecodedBarcode dataclass. |
| `tests/test_loader.py` | Tests for file format routing and image loading. |
| `tests/test_preprocessing.py` | Tests for OpenCV preprocessing pipeline. |
| `tests/test_decoder.py` | Tests for barcode decoding logic. |
| `tests/test_integration.py` | End-to-end: file in → decoded barcodes out. |

---

### Task 1: Project Dependencies and Package Scaffold

**Files:**
- Modify: `pyproject.toml`
- Create: `src/barcode_validator/__init__.py`
- Create: `src/barcode_validator/models.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Add dependencies via uv**

```bash
uv add PyMuPDF zxingcpp opencv-python Pillow
uv add --dev pytest
```

- [ ] **Step 2: Write failing test for DecodedBarcode**

```python
# tests/test_models.py
from barcode_validator.models import DecodedBarcode


def test_decoded_barcode_fields():
    bc = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert bc.value == "X001234567"
    assert bc.symbology == "CODE128"
    assert bc.page == 1


def test_decoded_barcode_equality():
    a = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    b = DecodedBarcode(value="X001234567", symbology="CODE128", page=1)
    assert a == b
```

```python
# tests/__init__.py
```

```python
# tests/conftest.py
from pathlib import Path

import pytest

TEST_DOCS = Path(__file__).parent.parent / "test_docs"


@pytest.fixture
def test_docs() -> Path:
    return TEST_DOCS


@pytest.fixture
def sample_pdf(test_docs) -> Path:
    return test_docs / "(proof)(BL6)(540841).pdf"


@pytest.fixture
def sample_ai(test_docs) -> Path:
    return test_docs / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai"


@pytest.fixture
def sample_jpg(test_docs) -> Path:
    return test_docs / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg"
```

- [ ] **Step 3: Run test to verify it fails**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'barcode_validator'`

- [ ] **Step 4: Create package scaffold and models**

```python
# src/barcode_validator/models.py
from dataclasses import dataclass


@dataclass(frozen=True)
class DecodedBarcode:
    """A single barcode decoded from an image."""
    value: str
    symbology: str
    page: int
```

```python
# src/barcode_validator/__init__.py
from barcode_validator.models import DecodedBarcode

__all__ = ["DecodedBarcode"]
```

Update `pyproject.toml` to add the package source:

```toml
[project]
# ... existing fields ...

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 5: Run test to verify it passes**

```bash
uv run pytest tests/test_models.py -v
```

Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add src/ tests/ pyproject.toml uv.lock
git commit -m "feat(epic-001): scaffold package with DecodedBarcode model and test fixtures"
```

---

### Task 2: File Format Routing and Image Loading

**Files:**
- Create: `src/barcode_validator/loader.py`
- Create: `tests/test_loader.py`

- [ ] **Step 1: Write failing tests for the loader**

```python
# tests/test_loader.py
from pathlib import Path

import pytest
from PIL import Image

from barcode_validator.loader import load_images, PageImage


def test_page_image_fields():
    img = Image.new("RGB", (100, 100))
    pi = PageImage(image=img, page=1)
    assert pi.page == 1
    assert pi.image.size == (100, 100)


def test_load_pdf(sample_pdf):
    pages = load_images(sample_pdf)
    assert len(pages) >= 1
    for p in pages:
        assert isinstance(p.image, Image.Image)
        assert p.page >= 1


def test_load_ai(sample_ai):
    pages = load_images(sample_ai)
    assert len(pages) >= 1
    assert pages[0].page == 1


def test_load_jpg(sample_jpg):
    pages = load_images(sample_jpg)
    assert len(pages) == 1
    assert pages[0].page == 1
    assert isinstance(pages[0].image, Image.Image)


def test_load_unsupported(tmp_path):
    bad_file = tmp_path / "file.xyz"
    bad_file.write_text("not a real file")
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_images(bad_file)


def test_load_nonexistent():
    with pytest.raises(FileNotFoundError):
        load_images(Path("/nonexistent/file.pdf"))
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_loader.py -v
```

Expected: `ImportError: cannot import name 'load_images' from 'barcode_validator.loader'`

- [ ] **Step 3: Implement the loader**

```python
# src/barcode_validator/loader.py
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

PDF_EXTENSIONS = {".pdf", ".ai"}
RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
PSD_EXTENSIONS = {".psd"}
SUPPORTED_EXTENSIONS = PDF_EXTENSIONS | RASTER_EXTENSIONS | PSD_EXTENSIONS


@dataclass
class PageImage:
    """An image extracted from a file, tagged with its page number."""
    image: Image.Image
    page: int


def load_images(file_path: Path) -> list[PageImage]:
    """Load a file and return a list of PIL Images with page numbers.

    Routes by file extension per ADR-006:
    - .pdf, .ai → PyMuPDF render at 2x scale
    - .psd → Pillow flattened composite
    - .png, .jpg, .jpeg, .tiff, .tif, .bmp → Pillow open
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext in PDF_EXTENSIONS:
        return _load_pdf(path)
    elif ext in PSD_EXTENSIONS:
        return _load_raster(path)
    elif ext in RASTER_EXTENSIONS:
        return _load_raster(path)
    else:
        raise ValueError(f"Unsupported file format: '{ext}'")


def _load_pdf(path: Path) -> list[PageImage]:
    """Render PDF/AI pages to images at 2x scale via PyMuPDF."""
    doc = fitz.open(str(path))
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        # 2x scale matrix for ~144-300 DPI rendering (ADR-002)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pages.append(PageImage(image=img, page=page_num + 1))
    doc.close()
    return pages


def _load_raster(path: Path) -> list[PageImage]:
    """Open a raster image or PSD flattened composite via Pillow."""
    img = Image.open(str(path))
    img.load()
    if img.mode != "RGB":
        img = img.convert("RGB")
    return [PageImage(image=img, page=1)]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_loader.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/loader.py tests/test_loader.py
git commit -m "feat(epic-001): file format routing and image loading (ADR-006)"
```

---

### Task 3: OpenCV Preprocessing Pipeline

**Files:**
- Create: `src/barcode_validator/preprocessing.py`
- Create: `tests/test_preprocessing.py`

- [ ] **Step 1: Write failing tests for preprocessing**

```python
# tests/test_preprocessing.py
import numpy as np
from PIL import Image

from barcode_validator.preprocessing import preprocess


def test_preprocess_returns_pil_image():
    img = Image.new("RGB", (200, 200), color=(128, 128, 128))
    result = preprocess(img)
    assert isinstance(result, Image.Image)


def test_preprocess_output_is_grayscale_binary():
    """Otsu threshold should produce a binary (black/white) image."""
    # Create a gradient image that will produce a clear threshold
    arr = np.zeros((100, 200, 3), dtype=np.uint8)
    arr[:, :100] = 255  # left half white
    arr[:, 100:] = 0    # right half black
    img = Image.fromarray(arr, "RGB")
    result = preprocess(img)
    result_arr = np.array(result)
    unique_values = set(np.unique(result_arr))
    assert unique_values <= {0, 255}


def test_preprocess_preserves_dimensions():
    img = Image.new("RGB", (300, 150))
    result = preprocess(img)
    assert result.size == (300, 150)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_preprocessing.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement preprocessing**

```python
# src/barcode_validator/preprocessing.py
import cv2
import numpy as np
from PIL import Image


def preprocess(image: Image.Image) -> Image.Image:
    """Apply preprocessing to improve barcode detection.

    Pipeline (ADR-003): Grayscale → Gaussian blur (5x5) → Otsu threshold.
    Returns a binary PIL Image suitable for barcode decoding retry.
    """
    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(binary)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_preprocessing.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/preprocessing.py tests/test_preprocessing.py
git commit -m "feat(epic-001): OpenCV preprocessing pipeline (ADR-003)"
```

---

### Task 4: Barcode Decoding with zxing-cpp and Preprocessing Retry

**Files:**
- Create: `src/barcode_validator/decoder.py`
- Create: `tests/test_decoder.py`

- [ ] **Step 1: Write failing tests for the decoder**

```python
# tests/test_decoder.py
from PIL import Image

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import PageImage
from barcode_validator.models import DecodedBarcode


def test_decode_returns_list():
    img = Image.new("RGB", (100, 100), color="white")
    page = PageImage(image=img, page=1)
    result = decode_barcodes([page])
    assert isinstance(result, list)


def test_decode_blank_image_returns_empty():
    """A blank white image has no barcodes."""
    img = Image.new("RGB", (200, 200), color="white")
    page = PageImage(image=img, page=1)
    result = decode_barcodes([page])
    assert result == []


def test_decode_preserves_page_number():
    """Page number from PageImage should carry through to DecodedBarcode."""
    img = Image.new("RGB", (100, 100), color="white")
    pages = [PageImage(image=img, page=3)]
    # No barcodes in blank image, but if there were, page should be 3
    result = decode_barcodes(pages)
    for bc in result:
        assert bc.page == 3


def test_decoded_barcode_has_required_fields():
    """Any DecodedBarcode must have value, symbology, and page."""
    img = Image.new("RGB", (100, 100))
    pages = [PageImage(image=img, page=1)]
    for bc in decode_barcodes(pages):
        assert isinstance(bc.value, str)
        assert isinstance(bc.symbology, str)
        assert isinstance(bc.page, int)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_decoder.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Implement the decoder**

```python
# src/barcode_validator/decoder.py
import zxingcpp
from PIL import Image

from barcode_validator.loader import PageImage
from barcode_validator.models import DecodedBarcode
from barcode_validator.preprocessing import preprocess


def _has_pyzbar() -> bool:
    """Check if pyzbar is available as optional fallback."""
    try:
        import pyzbar.pyzbar  # noqa: F401
        return True
    except ImportError:
        return False


def _zxing_decode(image: Image.Image) -> list[zxingcpp.Result]:
    """Decode barcodes from a PIL Image using zxing-cpp."""
    return zxingcpp.read_barcodes(image)


def _pyzbar_decode(image: Image.Image) -> list[DecodedBarcode]:
    """Decode barcodes using pyzbar as fallback."""
    from pyzbar.pyzbar import decode as pyzbar_decode

    results = pyzbar_decode(image)
    return [
        DecodedBarcode(
            value=r.data.decode("utf-8"),
            symbology=r.type,
            page=0,  # caller patches page number
        )
        for r in results
    ]


def _zxing_results_to_barcodes(
    results: list[zxingcpp.Result], page: int
) -> list[DecodedBarcode]:
    """Convert zxing-cpp results to DecodedBarcode instances."""
    return [
        DecodedBarcode(
            value=r.text,
            symbology=r.format.name,
            page=page,
        )
        for r in results
    ]


def decode_barcodes(pages: list[PageImage]) -> list[DecodedBarcode]:
    """Decode all barcodes from a list of page images.

    Strategy (ADR-001 + ADR-003):
    1. Try zxing-cpp on raw image
    2. If nothing found, preprocess (grayscale → blur → threshold) and retry zxing-cpp
    3. If still nothing and pyzbar is available, try pyzbar on raw image
    """
    all_barcodes: list[DecodedBarcode] = []

    for page_img in pages:
        barcodes = _decode_single_page(page_img)
        all_barcodes.extend(barcodes)

    return all_barcodes


def _decode_single_page(page_img: PageImage) -> list[DecodedBarcode]:
    """Decode barcodes from a single page image with retry pipeline."""
    image = page_img.image
    page = page_img.page

    # Step 1: Try zxing-cpp on raw image
    results = _zxing_decode(image)
    if results:
        return _zxing_results_to_barcodes(results, page)

    # Step 2: Preprocess and retry zxing-cpp
    preprocessed = preprocess(image)
    results = _zxing_decode(preprocessed)
    if results:
        return _zxing_results_to_barcodes(results, page)

    # Step 3: pyzbar fallback (if available)
    if _has_pyzbar():
        barcodes = _pyzbar_decode(image)
        return [
            DecodedBarcode(value=bc.value, symbology=bc.symbology, page=page)
            for bc in barcodes
        ]

    return []
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_decoder.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/decoder.py tests/test_decoder.py
git commit -m "feat(epic-001): barcode decoder with zxing-cpp, preprocessing retry, pyzbar fallback"
```

---

### Task 5: Top-Level `decode_file` Entry Point

**Files:**
- Modify: `src/barcode_validator/__init__.py`

- [ ] **Step 1: Write failing test for decode_file**

Add to a new integration-style test:

```python
# tests/test_decode_file.py
from pathlib import Path

import pytest

from barcode_validator import decode_file, DecodedBarcode


def test_decode_file_returns_list(sample_pdf):
    result = decode_file(sample_pdf)
    assert isinstance(result, list)
    for bc in result:
        assert isinstance(bc, DecodedBarcode)


def test_decode_file_nonexistent():
    with pytest.raises(FileNotFoundError):
        decode_file(Path("/nonexistent/file.pdf"))


def test_decode_file_unsupported(tmp_path):
    bad = tmp_path / "file.xyz"
    bad.write_text("nope")
    with pytest.raises(ValueError, match="Unsupported file format"):
        decode_file(bad)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_decode_file.py -v
```

Expected: `ImportError: cannot import name 'decode_file'`

- [ ] **Step 3: Implement decode_file**

```python
# src/barcode_validator/__init__.py
from pathlib import Path

from barcode_validator.decoder import decode_barcodes
from barcode_validator.loader import load_images
from barcode_validator.models import DecodedBarcode


def decode_file(file_path: Path) -> list[DecodedBarcode]:
    """Decode all barcodes from a label proof file.

    Accepts PDF, AI, PSD, PNG, JPG, TIFF, BMP.
    Returns a list of DecodedBarcode with value, symbology, and page number.
    """
    pages = load_images(file_path)
    return decode_barcodes(pages)


__all__ = ["decode_file", "DecodedBarcode"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_decode_file.py -v
```

Expected: all passed

- [ ] **Step 5: Commit**

```bash
git add src/barcode_validator/__init__.py tests/test_decode_file.py
git commit -m "feat(epic-001): decode_file entry point wiring loader → decoder"
```

---

### Task 6: Integration Tests Against Real Label Proofs

**Files:**
- Create: `tests/test_integration.py`

- [ ] **Step 1: Write integration tests**

```python
# tests/test_integration.py
"""Integration tests against real label proofs in test_docs/.

These tests verify the full pipeline: file → load → decode → DecodedBarcode list.
Expected values are ground-truth from manual barcode scanner verification.
"""
from pathlib import Path

import pytest

from barcode_validator import decode_file, DecodedBarcode


TEST_DOCS = Path(__file__).parent.parent / "test_docs"


@pytest.fixture
def skip_if_no_test_docs():
    if not TEST_DOCS.exists():
        pytest.skip("test_docs/ not available")


class TestPDFProofs:
    """Test decoding against real NCL PDF label proofs."""

    def test_proof_540841_decodes_barcodes(self, skip_if_no_test_docs):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = decode_file(path)
        assert len(result) > 0, "Expected at least one barcode in proof PDF"
        for bc in result:
            assert bc.value, "Barcode value should not be empty"
            assert bc.symbology, "Barcode symbology should not be empty"
            assert bc.page >= 1

    def test_proof_540837_decodes_barcodes(self, skip_if_no_test_docs):
        path = TEST_DOCS / "(proof)(BL6)(540837).pdf"
        result = decode_file(path)
        assert len(result) > 0, "Expected at least one barcode in proof PDF"

    def test_excel_printpack_0480_01(self, skip_if_no_test_docs):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-01 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)

    def test_excel_printpack_0480_04(self, skip_if_no_test_docs):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-04 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)


class TestAIFiles:
    """Test decoding AI files (PDF-compatible)."""

    def test_ai_file_decodes(self, skip_if_no_test_docs):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai"
        result = decode_file(path)
        assert isinstance(result, list)
        # AI file is PDF-compatible, should load without error
        # May or may not contain scannable barcodes depending on artwork


class TestRasterImages:
    """Test decoding raster images."""

    def test_jpg_loads_and_decodes(self, skip_if_no_test_docs):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg"
        result = decode_file(path)
        assert isinstance(result, list)
        for bc in result:
            assert bc.page == 1
```

- [ ] **Step 2: Run integration tests**

```bash
uv run pytest tests/test_integration.py -v
```

Expected: all passed (some tests may find 0 barcodes if artwork doesn't contain scannable barcodes — that's fine, the test asserts the pipeline runs without error)

- [ ] **Step 3: Inspect decoded values from real proofs**

Run a quick script to see what the pipeline actually decodes (for ground-truth verification):

```bash
uv run python -c "
from pathlib import Path
from barcode_validator import decode_file
for f in sorted(Path('test_docs').glob('*.pdf')):
    print(f'\n--- {f.name} ---')
    for bc in decode_file(f):
        print(f'  page={bc.page}  symbology={bc.symbology}  value={bc.value}')
"
```

Review the output. Update integration test assertions with actual ground-truth values if barcodes are decoded. If any expected barcodes are missing, that's a signal to investigate preprocessing or decoder config in a follow-up.

- [ ] **Step 4: Update integration tests with ground-truth assertions**

After reviewing output from Step 3, update the integration tests to assert specific barcode values. For example, if `(proof)(BL6)(540841).pdf` contains an FNSKU barcode with value `X00ABCDEFG`:

```python
def test_proof_540841_decodes_barcodes(self, skip_if_no_test_docs):
    path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
    result = decode_file(path)
    values = [bc.value for bc in result]
    # Replace with actual ground-truth values observed in Step 3
    assert "X00ABCDEFG" in values
```

- [ ] **Step 5: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass

- [ ] **Step 6: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat(epic-001): integration tests against real label proofs"
```

---

## Verification Checklist (EPIC-001 Definition of Done)

After all tasks are complete, verify each criterion:

- [ ] Given a PDF label proof from `test_docs/`, all barcodes on every page are decoded with correct raw values and symbology reported.
- [ ] Given a raster image (PNG/JPG) containing a barcode, the barcode is decoded correctly.
- [ ] If zxing-cpp misses a barcode, the preprocessing pipeline retries and the barcode is decoded on the second attempt.
- [ ] AI files with PDF compatibility and PSD files with flattened composites are handled without error.
- [ ] Unsupported file extensions return a clear error message.
- [ ] `uv run pytest -v` — all tests pass.
