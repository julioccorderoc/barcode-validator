"""Public barcode lookup — provider ABC and service orchestrator."""

from __future__ import annotations

from abc import ABC, abstractmethod

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
