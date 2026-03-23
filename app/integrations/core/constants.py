"""Shared GRC persistence constants (evidence ↔ control mapping, evidence_collections constraints)."""

from __future__ import annotations

# Laravel / polymorphic evidence mapping (evidence_mappeds.evidenceable_type)
CONTROL_EVIDENCEABLE_TYPE = "App\\Models\\Control"

# PostgreSQL CHECK on evidence_collections.evidence_from (see models_generated)
EVIDENCE_FROM_TOOL = "tool"
