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


@pytest.fixture
def unsupported_file(tmp_path) -> Path:
    f = tmp_path / "test.eps"
    f.write_bytes(b"%!PS-Adobe-3.0 EPSF-3.0")
    return f


@pytest.fixture
def missing_file() -> Path:
    return Path("nonexistent.pdf")
