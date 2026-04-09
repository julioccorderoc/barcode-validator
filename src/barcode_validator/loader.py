from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image

PDF_EXTENSIONS = {".pdf", ".ai"}
RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp"}
PSD_EXTENSIONS = {".psd"}


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
    with fitz.open(str(path)) as doc:
        pages = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 2x scale matrix for ~144-300 DPI rendering (ADR-002)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            pages.append(PageImage(image=img, page=page_num + 1))
    return pages


def _load_raster(path: Path) -> list[PageImage]:
    """Open a raster image or PSD flattened composite via Pillow."""
    img = Image.open(str(path))
    img.load()
    if img.mode != "RGB":
        img = img.convert("RGB")
    return [PageImage(image=img, page=1)]
