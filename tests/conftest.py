from pathlib import Path

import pytest

TEST_DOCS = Path(__file__).parent.parent / "test_docs"

# Ground-truth barcode values for each test_docs file.
# Fill in TODO entries with actual barcode values from manual verification.
# Format: {"value": str, "type": str (BarcodeType.value), "symbology": str}
GROUND_TRUTH: dict = {
    "(proof)(BL6)(540841).pdf": {
        "barcodes": [
            {"value": "0850031591271", "type": "EAN_13", "symbology": "EAN13"},
        ],
    },
    "(proof)(BL6)(540837).pdf": {
        "barcodes": [
            {"value": "0850031591264", "type": "EAN_13", "symbology": "EAN13"},
        ],
    },
    "EXCEL PRINTPACK-0480-01 proof.pdf": {
        "barcodes": [
            {"value": "X0032C5SUL", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "EXCEL PRINTPACK-0480-04 proof.pdf": {
        "barcodes": [
            {"value": "X002K7DQFD", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).ai": {
        "barcodes": [
            {"value": "X004781QUF", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
    "(label_artwork)(PH900X)(PH)(FNSKU_V3)(Level_Off).jpg": {
        "barcodes": [
            {"value": "X004781QUF", "type": "FNSKU", "symbology": "Code128"},
        ],
    },
}


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


@pytest.fixture
def unsupported_file(tmp_path) -> Path:
    f = tmp_path / "test.eps"
    f.write_bytes(b"%!PS-Adobe-3.0 EPSF-3.0")
    return f


@pytest.fixture
def missing_file() -> Path:
    return Path("nonexistent.pdf")
