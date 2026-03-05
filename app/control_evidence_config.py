"""
Control -> required evidence type codes (file-based; no DB table).
Reads app/evidence_config/control_evidence_requirements.json.
"""

import json
from pathlib import Path
from uuid import UUID

_requirements: dict[str, list[str]] | None = None


def _path() -> Path:
    return Path(__file__).parent / "evidence_config" / "control_evidence_requirements.json"


def load_control_evidence_requirements() -> dict[str, list[str]]:
    """control_id (str) -> list of evidence_type codes. Cached after first load."""
    global _requirements
    if _requirements is not None:
        return _requirements
    p = _path()
    if not p.exists():
        _requirements = {}
        return _requirements
    with open(p, encoding="utf-8") as f:
        _requirements = json.load(f)
    return _requirements


def get_required_evidence_types_for_control(control_id: str | UUID) -> list[str]:
    """Return list of evidence_type codes required for the given control."""
    req = load_control_evidence_requirements()
    key = str(control_id)
    return list(req.get(key, []))
