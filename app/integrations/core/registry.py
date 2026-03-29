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
    HRMS (Zoho People) and IDP (Microsoft Entra commercial + GCC High) are registered at import time.
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
        display_name="Zoho People (HR / Employee Management)",
        description="HR and employee-lifecycle evidence via Zoho People APIs (OAuth, Forms, Attendance, Leave, LMS; see api_endpoints.py).",
    )
)
registry.register(
    ProviderMeta(
        category=IntegrationCategory.IDP,
        key="microsoft_entra",
        display_name="Microsoft Entra ID",
        description="Identity evidence via Microsoft Graph (commercial cloud; OAuth + collectors).",
    )
)
registry.register(
    ProviderMeta(
        category=IntegrationCategory.IDP,
        key="microsoft_entra_gcc_high",
        display_name="Microsoft Entra ID (GCC High)",
        description="Identity evidence via Microsoft Graph US sovereign cloud (OAuth + collectors).",
    )
)
registry.register(
    ProviderMeta(
        category=IntegrationCategory.ITSM,
        key="jira_cloud",
        display_name="Jira Cloud",
        description="ITSM evidence via Jira Cloud APIs (OAuth + collectors).",
    )
)
registry.register(
    ProviderMeta(
        category=IntegrationCategory.ITSM,
        key="linear",
        display_name="Linear",
        description="ITSM evidence and issues via Linear GraphQL API (OAuth + collectors).",
    )
)
