"""Public barcode lookup — provider ABC and service orchestrator."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from urllib.request import urlopen, Request

from barcode_validator.models import BarcodeType, LookupResult


class LookupProvider(ABC):
    """Abstract base class for barcode lookup providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'open_food_facts')."""

    @property
    @abstractmethod
    def supported_types(self) -> set[BarcodeType]:
        """Barcode types this provider can look up."""

    @abstractmethod
    def lookup(self, value: str) -> LookupResult | None:
        """Look up a barcode value. Returns LookupResult or None if not found."""


class LookupService:
    """Orchestrates barcode lookups across multiple providers."""

    def __init__(self, providers: list[LookupProvider]) -> None:
        self._providers = providers

    def lookup(self, value: str, barcode_type: BarcodeType) -> LookupResult | None:
        """Look up a barcode value using registered providers.

        Tries providers in order. Returns the first hit, or None.
        """
        for provider in self._providers:
            if barcode_type not in provider.supported_types:
                continue
            result = provider.lookup(value)
            if result is not None:
                return result
        return None


class OpenFoodFactsProvider(LookupProvider):
    """Lookup via Open Food Facts API (free, no auth)."""

    API_URL = "https://world.openfoodfacts.net/api/v2/product/{barcode}"

    @property
    def name(self) -> str:
        return "open_food_facts"

    @property
    def supported_types(self) -> set[BarcodeType]:
        return {BarcodeType.UPC_A, BarcodeType.EAN_13, BarcodeType.EAN_8}

    def lookup(self, value: str) -> LookupResult | None:
        url = self.API_URL.format(barcode=value)
        request = Request(url, headers={"User-Agent": "barcode-validator/0.1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
        except (OSError, json.JSONDecodeError):
            return None

        if data.get("status") != 1:
            return None

        product = data.get("product", {})
        return LookupResult(
            found=True,
            product_name=product.get("product_name") or None,
            brand=product.get("brands") or None,
            category=product.get("categories") or None,
            source=self.name,
        )


class UPCitemdbProvider(LookupProvider):
    """Lookup via UPCitemdb API (free tier, 100 req/day, no auth)."""

    API_URL = "https://api.upcitemdb.com/prod/trial/lookup?upc={barcode}"

    @property
    def name(self) -> str:
        return "upcitemdb"

    @property
    def supported_types(self) -> set[BarcodeType]:
        return {
            BarcodeType.UPC_A,
            BarcodeType.EAN_13,
            BarcodeType.EAN_8,
            BarcodeType.UPC_E,
            BarcodeType.ISBN_13,
        }

    def lookup(self, value: str) -> LookupResult | None:
        url = self.API_URL.format(barcode=value)
        request = Request(url, headers={"User-Agent": "barcode-validator/0.1.0"})
        try:
            with urlopen(request, timeout=10) as response:
                data = json.loads(response.read())
        except (OSError, json.JSONDecodeError):
            return None

        items = data.get("items", [])
        if not items:
            return None

        item = items[0]
        return LookupResult(
            found=True,
            product_name=item.get("title") or None,
            brand=item.get("brand") or None,
            category=item.get("category") or None,
            source=self.name,
        )


def create_lookup_service() -> LookupService:
    """Create a LookupService with the default built-in providers."""
    return LookupService([
        OpenFoodFactsProvider(),
        UPCitemdbProvider(),
    ])
