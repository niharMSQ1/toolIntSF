"""Core abstractions: categories, protocols, registry, shared constants, generic persistence."""

from app.integrations.core.category import IntegrationCategory
from app.integrations.core.constants import CONTROL_EVIDENCEABLE_TYPE, EVIDENCE_FROM_TOOL
from app.integrations.core.registry import IntegrationProviderRegistry, ProviderMeta, registry

__all__ = [
    "CONTROL_EVIDENCEABLE_TYPE",
    "EVIDENCE_FROM_TOOL",
    "IntegrationCategory",
    "IntegrationProviderRegistry",
    "ProviderMeta",
    "registry",
]
