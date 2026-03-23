"""Registry for future multi-provider wiring (category + platform key → metadata)."""

from __future__ import annotations

from dataclasses import dataclass

from app.integrations.core.category import IntegrationCategory


@dataclass(frozen=True)
class ProviderMeta:
    """Describes a registered integration provider (extend when adding IDP, ITSM, etc.)."""

    category: IntegrationCategory
    key: str
    display_name: str
    description: str = ""


class IntegrationProviderRegistry:
    """
    In-process registry of known providers.
    HRMS / Zoho People is registered at import time; add IDP/Okta-style providers here later.
    """

    def __init__(self) -> None:
        self._providers: dict[tuple[str, str], ProviderMeta] = {}

    def register(self, meta: ProviderMeta) -> None:
        self._providers[(meta.category.value, meta.key)] = meta

    def get(self, category: IntegrationCategory, key: str) -> ProviderMeta | None:
        return self._providers.get((category.value, key))

    def all(self) -> tuple[ProviderMeta, ...]:
        return tuple(self._providers.values())


registry = IntegrationProviderRegistry()
registry.register(
    ProviderMeta(
        category=IntegrationCategory.HRMS,
        key="zoho_people",
        display_name="Zoho People",
        description="HR evidence via Zoho People APIs (OAuth + collectors).",
    )
)
