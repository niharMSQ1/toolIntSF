"""
Microsoft Entra ID (commercial + GCC High).

- Vanta-style credentials: set ``ENTRA_*`` / ``ENTRA_GCC_HIGH_*`` in environment (see ``app.config.Settings``).
- OAuth, Graph collectors, evidence + control mapping via shared GRC persistence.

Provider keys: ``microsoft_entra`` (commercial), ``microsoft_entra_gcc_high`` (GCC High).
"""

PROVIDER_KEY = "microsoft_entra"
PROVIDER_KEY_GCC_HIGH = "microsoft_entra_gcc_high"

__all__ = ["PROVIDER_KEY", "PROVIDER_KEY_GCC_HIGH"]
