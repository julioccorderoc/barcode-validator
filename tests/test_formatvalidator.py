"""Tests for format validation of barcode values."""
from barcode_validator.formatvalidator import validate_format
from barcode_validator.models import BarcodeType


class TestFormatFNSKU:
    def test_format_fnsku_valid(self):
        assert validate_format("X004781QUF", BarcodeType.FNSKU) is True

    def test_format_fnsku_invalid_prefix(self):
        assert validate_format("Y001234567", BarcodeType.FNSKU) is False

    def test_format_fnsku_invalid_length(self):
        assert validate_format("X0012345", BarcodeType.FNSKU) is False

    def test_format_fnsku_invalid_lowercase(self):
        assert validate_format("X004781quf", BarcodeType.FNSKU) is False


class TestFormatUPCA:
    def test_format_upca_valid(self):
        assert validate_format("012345678905", BarcodeType.UPC_A) is True

    def test_format_upca_invalid_alpha(self):
        assert validate_format("01234567890A", BarcodeType.UPC_A) is False

    def test_format_upca_invalid_length(self):
        assert validate_format("01234567890", BarcodeType.UPC_A) is False


class TestFormatEAN13:
    def test_format_ean13_valid(self):
        assert validate_format("0850031591271", BarcodeType.EAN_13) is True

    def test_format_ean13_invalid(self):
        assert validate_format("085003159127", BarcodeType.EAN_13) is False


class TestFormatISBN13:
    def test_format_isbn13_valid_978(self):
        assert validate_format("9780134685991", BarcodeType.ISBN_13) is True

    def test_format_isbn13_valid_979(self):
        assert validate_format("9791234567890", BarcodeType.ISBN_13) is True

    def test_format_isbn13_invalid_prefix(self):
        assert validate_format("9770134685991", BarcodeType.ISBN_13) is False


class TestFormatEAN8:
    def test_format_ean8_valid(self):
        assert validate_format("96385074", BarcodeType.EAN_8) is True


class TestFormatUPCE:
    def test_format_upce_valid(self):
        assert validate_format("01234565", BarcodeType.UPC_E) is True


class TestFormatASIN:
    def test_format_asin_valid(self):
        assert validate_format("B08N5WRWNW", BarcodeType.ASIN) is True

    def test_format_asin_invalid_prefix(self):
        assert validate_format("A08N5WRWNW", BarcodeType.ASIN) is False


class TestFormatCode128:
    def test_format_code128_valid(self):
        assert validate_format("Hello World 123!", BarcodeType.CODE128) is True

    def test_format_code128_invalid_control(self):
        assert validate_format("Hello\x01World", BarcodeType.CODE128) is False


class TestFormatCode39:
    def test_format_code39_valid(self):
        assert validate_format("HELLO-123", BarcodeType.CODE39) is True

    def test_format_code39_invalid_lowercase(self):
        assert validate_format("hello", BarcodeType.CODE39) is False


class TestFormatUnknown:
    def test_format_unknown_nonempty(self):
        assert validate_format("anything", BarcodeType.UNKNOWN) is True

    def test_format_unknown_empty(self):
        assert validate_format("", BarcodeType.UNKNOWN) is False
