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
