"""Tests for the lookup module — providers and service."""

from barcode_validator.lookup import LookupProvider, LookupService
from barcode_validator.models import BarcodeType, LookupResult


class FakeProvider(LookupProvider):
    """Test provider that returns a fixed result."""

    def __init__(self, name: str, supported: set[BarcodeType], result: LookupResult | None):
        self._name = name
        self._supported = supported
        self._result = result

    @property
    def name(self) -> str:
        return self._name

    @property
    def supported_types(self) -> set[BarcodeType]:
        return self._supported

    def lookup(self, value: str) -> LookupResult | None:
        return self._result


FOUND_RESULT = LookupResult(
    found=True,
    product_name="Test Product",
    brand="Test Brand",
    category="Food",
    source="fake",
)


def test_service_returns_first_provider_hit():
    provider = FakeProvider("fake", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([provider])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is not None
    assert result.found is True
    assert result.product_name == "Test Product"


def test_service_skips_provider_that_does_not_support_type():
    provider = FakeProvider("fake", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([provider])
    result = service.lookup("X00ABC1234", BarcodeType.FNSKU)
    assert result is None


def test_service_tries_fallback_on_miss():
    miss = FakeProvider("miss", {BarcodeType.UPC_A}, None)
    hit = FakeProvider("hit", {BarcodeType.UPC_A}, FOUND_RESULT)
    service = LookupService([miss, hit])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is not None
    assert result.source == "fake"


def test_service_returns_none_when_all_miss():
    miss1 = FakeProvider("miss1", {BarcodeType.UPC_A}, None)
    miss2 = FakeProvider("miss2", {BarcodeType.UPC_A}, None)
    service = LookupService([miss1, miss2])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is None


def test_service_returns_none_for_empty_providers():
    service = LookupService([])
    result = service.lookup("012345678901", BarcodeType.UPC_A)
    assert result is None
