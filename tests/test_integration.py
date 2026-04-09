"""Integration tests against real label proofs in test_docs/.

These tests verify the full pipeline: file → load → decode → DecodedBarcode list.
Expected values are ground-truth from manual verification.
"""
from pathlib import Path

import pytest

from barcode_validator import decode_file, DecodedBarcode

TEST_DOCS = Path(__file__).parent.parent / "test_docs"

pytestmark = pytest.mark.skipif(
    not TEST_DOCS.exists(), reason="test_docs/ not available"
)


class TestPDFProofs:
    """Test decoding against real NCL PDF label proofs."""

    def test_proof_540841_decodes_ean13(self):
        path = TEST_DOCS / "(proof)(BL6)(540841).pdf"
        result = decode_file(path)
        assert len(result) >= 1
        values = [bc.value for bc in result]
        assert "0850031591271" in values
        bc = next(b for b in result if b.value == "0850031591271")
        assert bc.symbology == "EAN13"
        assert bc.page == 1

    def test_proof_540837_no_barcodes_detected(self):
        path = TEST_DOCS / "(proof)(BL6)(540837).pdf"
        result = decode_file(path)
        assert result == []

    def test_excel_printpack_0480_01_runs_without_error(self):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-01 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)

    def test_excel_printpack_0480_04_runs_without_error(self):
        path = TEST_DOCS / "EXCEL PRINTPACK-0480-04 proof.pdf"
        result = decode_file(path)
        assert isinstance(result, list)


class TestAIFiles:
    """Test decoding AI files (PDF-compatible)."""

    def test_ai_file_runs_without_error(self):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai"
        result = decode_file(path)
        assert isinstance(result, list)


class TestRasterImages:
    """Test decoding raster images."""

    def test_jpg_decodes_fnsku(self):
        path = TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg"
        result = decode_file(path)
        assert len(result) >= 1
        values = [bc.value for bc in result]
        assert "X004781QUF" in values
        bc = next(b for b in result if b.value == "X004781QUF")
        assert bc.symbology == "Code128"
        assert bc.page == 1
