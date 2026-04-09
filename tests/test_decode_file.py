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
