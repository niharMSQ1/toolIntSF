"""
AWS cloud infrastructure integration.

- ``client``: boto3 session/client helpers and credential validation.
- ``collector``: evidence-master-name to AWS API mapping.
- ``collection_runner``: domain-driven G4/G5 persistence flow.
- ``routers``: configure endpoint and explicit collect endpoint.
"""

PROVIDER_KEY = "aws"

__all__ = ["PROVIDER_KEY"]
