"""Tests for check digit validation."""

import pytest

from barcode_validator.checkdigit import validate_checkdigit, _mod10_check
from barcode_validator.models import BarcodeType


class TestMod10Check:
    """Tests for the MOD 10 (GTIN) check digit algorithm."""

    def test_mod10_ean13_valid(self):
        assert _mod10_check("0850031591271") is True

    def test_mod10_ean13_invalid(self):
        assert _mod10_check("0850031591270") is False

    def test_mod10_upca_valid(self):
        assert _mod10_check("012345678905") is True

    def test_mod10_upca_invalid(self):
        assert _mod10_check("012345678900") is False

    def test_mod10_isbn13_valid(self):
        assert _mod10_check("9780134685991") is True

    def test_mod10_isbn13_invalid(self):
        assert _mod10_check("9780134685990") is False

    def test_mod10_ean8_valid(self):
        assert _mod10_check("96385074") is True

    def test_mod10_ean8_invalid(self):
        assert _mod10_check("96385070") is False

    def test_mod10_upce_valid(self):
        assert _mod10_check("01234565") is True


class TestValidateCheckdigit:
    """Tests for the validate_checkdigit dispatch function."""

    def test_checkdigit_fnsku_returns_none(self):
        assert validate_checkdigit("X001234567", BarcodeType.FNSKU) is None

    def test_checkdigit_asin_returns_none(self):
        assert validate_checkdigit("B000000001", BarcodeType.ASIN) is None

    def test_checkdigit_code128_returns_none(self):
        assert validate_checkdigit("ABC123", BarcodeType.CODE128) is None

    def test_checkdigit_unknown_returns_none(self):
        assert validate_checkdigit("anything", BarcodeType.UNKNOWN) is None

    def test_upca_dispatches_mod10(self):
        assert validate_checkdigit("012345678905", BarcodeType.UPC_A) is True
        assert validate_checkdigit("012345678900", BarcodeType.UPC_A) is False

    def test_ean13_dispatches_mod10(self):
        assert validate_checkdigit("0850031591271", BarcodeType.EAN_13) is True

    def test_ean8_dispatches_mod10(self):
        assert validate_checkdigit("96385074", BarcodeType.EAN_8) is True

    def test_isbn13_dispatches_mod10(self):
        assert validate_checkdigit("9780134685991", BarcodeType.ISBN_13) is True

    def test_upce_dispatches_mod10(self):
        assert validate_checkdigit("01234565", BarcodeType.UPC_E) is True
