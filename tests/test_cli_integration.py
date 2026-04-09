"""Integration tests for CLI against real label proofs in test_docs/.

Tests the full CLI path: argv → parse → validate_label → output → exit code.
No mocks — exercises the real pipeline end-to-end.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from barcode_validator.cli import main

TEST_DOCS = Path(__file__).parent.parent / "test_docs"

pytestmark = pytest.mark.skipif(
    not TEST_DOCS.exists(), reason="test_docs/ not available"
)


class TestDecodeOnly:
    """CLI decode-only mode against real files."""

    def test_pdf_decode_exit_0(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([pdf])
        assert code == 0
        captured = capsys.readouterr()
        assert "0850031591271" in captured.err
        assert captured.out == ""

    def test_pdf_json_to_stdout(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([pdf, "--json"])
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["passed"] is True
        assert data["mode"] == "decode"
        assert any(bc["value"] == "0850031591271" for bc in data["barcodes"])
        assert captured.err == ""

    def test_jpg_decode(self, capsys):
        jpg = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg")
        code = main([jpg])
        assert code == 0
        captured = capsys.readouterr()
        assert "X004781QUF" in captured.err


class TestComparison:
    """CLI comparison mode against real files."""

    def test_expected_match_exit_0(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([pdf, "--expected", "0850031591271"])
        assert code == 0

    def test_expected_mismatch_exit_1(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([pdf, "--expected", "WRONG"])
        assert code == 1

    def test_comparison_json_output(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([pdf, "--expected", "0850031591271", "--json"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["mode"] == "comparison"
        assert data["expected_not_found"] == []


class TestErrorPaths:
    """CLI error handling with exit code 2."""

    def test_missing_file_exit_2(self, capsys):
        code = main(["nonexistent.pdf"])
        assert code == 2
        assert "Error" in capsys.readouterr().err

    def test_unsupported_format_exit_2(self, capsys, unsupported_file):
        code = main([str(unsupported_file)])
        assert code == 2
        assert "Error" in capsys.readouterr().err


class TestEntryPoints:
    """Verify package entry points work."""

    def test_python_m_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "barcode_validator", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "barcode-validator" in result.stdout or "usage" in result.stdout.lower()

    def test_console_script_help(self):
        result = subprocess.run(
            ["barcode-validator", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "barcode-validator" in result.stdout or "usage" in result.stdout.lower()


class TestBatchRealFiles:
    """Batch mode with multiple real files."""

    def test_batch_two_pdfs(self, capsys):
        pdf1 = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        pdf2 = str(TEST_DOCS / "(proof)(BL6)(540837).pdf")
        code = main([pdf1, pdf2])
        assert code in (0, 1)

    def test_batch_pdf_and_jpg(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        jpg = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg")
        code = main([pdf, jpg])
        assert code == 0

    def test_batch_json_multiple_files(self, capsys):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        jpg = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg")
        code = main([pdf, jpg, "--json"])
        captured = capsys.readouterr()
        assert "0850031591271" in captured.out
        assert "X004781QUF" in captured.out

    def test_batch_mixed_valid_and_error(self, capsys, unsupported_file):
        pdf = str(TEST_DOCS / "(proof)(BL6)(540841).pdf")
        code = main([str(unsupported_file), pdf, "--json"])
        assert code == 2
        captured = capsys.readouterr()
        assert "0850031591271" in captured.out
        assert "Error" in captured.err


class TestAIFileCLI:
    """AI file format through CLI."""

    def test_ai_file_decode(self, capsys):
        ai = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai")
        code = main([ai])
        assert code in (0, 1)

    def test_ai_file_json(self, capsys):
        ai = str(TEST_DOCS / "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai")
        code = main([ai, "--json"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "file" in data
        assert "barcodes" in data
        assert "passed" in data
        assert "mode" in data
