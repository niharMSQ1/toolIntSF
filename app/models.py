"""
Stable import aliases for ORM classes defined in `models_generated.py`.

Regenerate the full schema with `python generate_model.py` from the project root.
Application code should import from `app.models` (not `models_generated` directly).
"""

from __future__ import annotations

from app.models_generated import (
    Base,
    ControlEvidenceMaster,
    Evidence,
    EvidenceCollections,
    EvidenceMasters,
    EvidenceMappeds,
    ToolIntegrations,
    Tools,
)

# Singular names used across services
ToolIntegration = ToolIntegrations
EvidenceMaster = EvidenceMasters
EvidenceCollection = EvidenceCollections
EvidenceMapped = EvidenceMappeds

__all__ = [
    "Base",
    "ControlEvidenceMaster",
    "Evidence",
    "EvidenceCollection",
    "EvidenceCollections",
    "EvidenceMapped",
    "EvidenceMappeds",
    "EvidenceMaster",
    "EvidenceMasters",
    "ToolIntegration",
    "ToolIntegrations",
    "Tools",
]
