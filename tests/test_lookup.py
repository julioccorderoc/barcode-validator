"""Tests for the lookup module — providers and service."""

import json
from unittest.mock import patch, MagicMock

import pytest

from barcode_validator.lookup import LookupProvider, LookupService, OpenFoodFactsProvider, UPCitemdbProvider, create_lookup_service
from barcode_validator.models import BarcodeType, LookupResult


def _mock_urlopen(response_data: dict, status: int = 200):
    """Create a mock for urllib.request.urlopen."""
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.read.return_value = json.dumps(response_data).encode("utf-8")
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


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


class TestOpenFoodFactsProvider:
    def test_supported_types(self):
        provider = OpenFoodFactsProvider()
        assert BarcodeType.UPC_A in provider.supported_types
        assert BarcodeType.EAN_13 in provider.supported_types
        assert BarcodeType.EAN_8 in provider.supported_types
        assert BarcodeType.FNSKU not in provider.supported_types
        assert BarcodeType.ASIN not in provider.supported_types

    def test_name(self):
        provider = OpenFoodFactsProvider()
        assert provider.name == "open_food_facts"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "status": 1,
            "product": {
                "product_name": "Organic Coconut Oil",
                "brands": "Nature's Best",
                "categories": "Oils, Coconut oils",
            },
        })
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0850031591271")
        assert result is not None
        assert result.found is True
        assert result.product_name == "Organic Coconut Oil"
        assert result.brand == "Nature's Best"
        assert result.category == "Oils, Coconut oils"
        assert result.source == "open_food_facts"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_not_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({"status": 0})
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0000000000000")
        assert result is None

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_network_error(self, mock_urlopen_fn):
        mock_urlopen_fn.side_effect = OSError("Network unreachable")
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0850031591271")
        assert result is None


class TestUPCitemdbProvider:
    def test_supported_types(self):
        provider = UPCitemdbProvider()
        assert BarcodeType.UPC_A in provider.supported_types
        assert BarcodeType.EAN_13 in provider.supported_types
        assert BarcodeType.EAN_8 in provider.supported_types
        assert BarcodeType.UPC_E in provider.supported_types
        assert BarcodeType.ISBN_13 in provider.supported_types
        assert BarcodeType.FNSKU not in provider.supported_types

    def test_name(self):
        provider = UPCitemdbProvider()
        assert provider.name == "upcitemdb"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "code": "OK",
            "total": 1,
            "items": [{
                "title": "Coconut Oil Organic",
                "brand": "Nature's Best",
                "category": "Health & Beauty",
            }],
        })
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        assert result is not None
        assert result.found is True
        assert result.product_name == "Coconut Oil Organic"
        assert result.brand == "Nature's Best"
        assert result.category == "Health & Beauty"
        assert result.source == "upcitemdb"

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_not_found(self, mock_urlopen_fn):
        mock_urlopen_fn.return_value = _mock_urlopen({
            "code": "OK",
            "total": 0,
            "items": [],
        })
        provider = UPCitemdbProvider()
        result = provider.lookup("0000000000000")
        assert result is None

    @patch("barcode_validator.lookup.urlopen")
    def test_lookup_network_error(self, mock_urlopen_fn):
        mock_urlopen_fn.side_effect = OSError("Connection refused")
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        assert result is None


def test_create_lookup_service_returns_service_with_default_providers():
    service = create_lookup_service()
    assert isinstance(service, LookupService)
    assert len(service._providers) == 2
    assert service._providers[0].name == "open_food_facts"
    assert service._providers[1].name == "upcitemdb"


@pytest.mark.network
class TestOpenFoodFactsIntegration:
    """Integration tests hitting the real Open Food Facts API."""

    def test_real_lookup_known_ean(self):
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0850031591271")
        if result is not None:
            assert result.found is True
            assert result.source == "open_food_facts"

    def test_real_lookup_unknown_barcode(self):
        provider = OpenFoodFactsProvider()
        result = provider.lookup("0000000000000")
        assert result is None


@pytest.mark.network
class TestUPCitemdbIntegration:
    """Integration tests hitting the real UPCitemdb API."""

    def test_real_lookup_known_ean(self):
        provider = UPCitemdbProvider()
        result = provider.lookup("0850031591271")
        if result is not None:
            assert result.found is True
            assert result.source == "upcitemdb"
