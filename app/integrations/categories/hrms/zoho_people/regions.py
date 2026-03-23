from __future__ import annotations

# Zoho Accounts OAuth base URLs by region key (see Zoho multi-DC docs).
ACCOUNTS_BASE_BY_REGION: dict[str, str] = {
    "us": "https://accounts.zoho.com",
    "com": "https://accounts.zoho.com",
    "in": "https://accounts.zoho.in",
    "eu": "https://accounts.zoho.eu",
    "au": "https://accounts.zoho.com.au",
    "jp": "https://accounts.zoho.jp",
    "ca": "https://accounts.zohocloud.ca",
    "sa": "https://accounts.zoho.sa",
    "uk": "https://accounts.zoho.uk",
}

PEOPLE_BASE_BY_REGION: dict[str, str] = {
    "us": "https://people.zoho.com",
    "com": "https://people.zoho.com",
    "in": "https://people.zoho.in",
    "eu": "https://people.zoho.eu",
    "au": "https://people.zoho.com.au",
    "jp": "https://people.zoho.jp",
    "ca": "https://people.zoho.com",
    "sa": "https://people.zoho.sa",
    "uk": "https://people.zoho.uk",
}


def normalize_region(region: str) -> str:
    r = region.strip().lower()
    if r in ACCOUNTS_BASE_BY_REGION:
        return r
    return "com"


def accounts_base_url(region: str) -> str:
    return ACCOUNTS_BASE_BY_REGION.get(normalize_region(region), ACCOUNTS_BASE_BY_REGION["com"])


def people_base_url(region: str) -> str:
    return PEOPLE_BASE_BY_REGION.get(normalize_region(region), PEOPLE_BASE_BY_REGION["com"])
