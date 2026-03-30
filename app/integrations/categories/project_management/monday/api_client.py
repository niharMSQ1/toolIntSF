"""Monday.com GraphQL client — POST https://api.monday.com/v2"""

from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.integrations.categories.project_management.monday.constants import MONDAY_API_URL, MONDAY_API_VERSION

_MAX_RETRIES = 6


def graphql(
    token: str,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Execute GraphQL. Raises httpx.HTTPStatusError on HTTP errors.
    Monday returns 200 with `errors` array for GraphQL errors.
    """
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "API-Version": MONDAY_API_VERSION,
    }
    body: dict[str, Any] = {"query": query}
    if variables:
        body["variables"] = variables
    last: httpx.Response | None = None
    for attempt in range(_MAX_RETRIES):
        with httpx.Client(timeout=120.0) as client:
            r = client.post(MONDAY_API_URL, headers=headers, content=json.dumps(body))
        last = r
        if r.status_code == 429:
            ra = r.headers.get("Retry-After")
            try:
                delay = float(ra) if ra else 2.0
            except ValueError:
                delay = 2.0
            time.sleep(min(delay, 60.0))
            continue
        r.raise_for_status()
        return r.json()
    if last is not None:
        last.raise_for_status()
    raise RuntimeError("Monday GraphQL request failed")


def graphql_data(token: str, query: str, *, variables: dict[str, Any] | None = None) -> dict[str, Any] | None:
    payload = graphql(token, query, variables=variables)
    err = payload.get("errors")
    if isinstance(err, list) and err:
        first = err[0] if err else {}
        msg = first.get("message") if isinstance(first, dict) else str(err)
        raise ValueError(f"Monday GraphQL error: {msg}")
    data = payload.get("data")
    if isinstance(data, dict):
        return data
    return None


def get_me(token: str) -> dict[str, Any]:
    q = """
    query {
      me {
        id
        name
        email
        photo_original
      }
    }
    """
    data = graphql_data(token, q)
    return data.get("me") if data else {}


def list_boards(token: str, *, limit: int = 50) -> list[dict[str, Any]]:
    q = """
    query ($limit: Int!) {
      boards (limit: $limit) {
        id
        name
        state
        board_kind
      }
    }
    """
    data = graphql_data(token, q, variables={"limit": min(limit, 100)})
    boards = (data or {}).get("boards")
    if isinstance(boards, list):
        return [b for b in boards if isinstance(b, dict)]
    return []


def list_items_for_board(
    token: str,
    board_id: str,
    *,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """Uses items_page on board — https://developer.monday.com/api-reference/reference/boards"""
    q = """
    query ($board_ids: [ID!], $limit: Int!) {
      boards (ids: $board_ids) {
        id
        items_page (limit: $limit) {
          items {
            id
            name
            state
            column_values {
              id
              text
              type
              value
            }
          }
        }
      }
    }
    """
    data = graphql_data(
        token,
        q,
        variables={"board_ids": [board_id], "limit": min(limit, 500)},
    )
    boards = (data or {}).get("boards")
    if not isinstance(boards, list) or not boards:
        return []
    b0 = boards[0]
    if not isinstance(b0, dict):
        return []
    page = b0.get("items_page")
    if not isinstance(page, dict):
        return []
    items = page.get("items")
    if isinstance(items, list):
        return [x for x in items if isinstance(x, dict)]
    return []
