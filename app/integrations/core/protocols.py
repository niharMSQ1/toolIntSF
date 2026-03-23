"""Structural typing (Protocol) for integration providers — enables SOLID dependency inversion."""

from __future__ import annotations

from typing import Any, Protocol

from sqlalchemy.orm import Session


class EvidenceCollector(Protocol):
    """Pulls raw evidence payload for one evidence master row (tool-specific)."""

    def collect_for_master(
        self,
        master: dict[str, Any],
        cfg: dict[str, Any],
        *,
        date_from: str | None,
        date_to: str | None,
    ) -> dict[str, Any]: ...


class OAuthTokenRefresher(Protocol):
    """Refreshes OAuth access tokens stored on tool_integrations.configuration_data."""

    def refresh_access_tokens(
        self,
        session: Session,
        integration: dict[str, Any],
        *,
        force: bool = False,
    ) -> tuple[dict[str, Any], bool]: ...
