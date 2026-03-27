"""Collect evidence payloads from Bitbucket Cloud by ``evidence_masters.code`` (EV-*)."""

from __future__ import annotations

from typing import Any

from app.integrations.categories.devtools.bitbucket import api_client
from app.integrations.categories.devtools.bitbucket.evidence_map import EVIDENCE_CODE_STRATEGY


def _selected_slugs(cfg: dict[str, Any]) -> list[str]:
    raw = cfg.get("selected_workspaces")
    if not isinstance(raw, list):
        return []
    slugs: list[str] = []
    for w in raw:
        if isinstance(w, dict) and w.get("slug"):
            slugs.append(str(w["slug"]))
        elif isinstance(w, str) and w.strip():
            slugs.append(w.strip())
    return slugs


def _not_applicable(code: str, *, reason: str | None = None) -> dict[str, Any]:
    return {
        "evidence_code": code,
        "integration": "bitbucket_cloud",
        "collectable_via_bitbucket_api": False,
        "message": reason
        or "This evidence type is not available from Bitbucket Cloud REST APIs; use the owning system or another integration.",
    }


def _per_repo_bundle(
    workspace_slugs: list[str],
    access_token: str,
    *,
    fn: Any,
    max_repos_per_workspace: int = 25,
) -> dict[str, Any]:
    out: dict[str, Any] = {"workspaces": {}}
    for ws in workspace_slugs:
        wdata: dict[str, Any] = {"repositories": {}}
        try:
            repos = api_client.list_repositories(ws, access_token, max_repos=max_repos_per_workspace)
        except Exception as e:  # noqa: BLE001
            wdata["error"] = str(e)[:2000]
            out["workspaces"][ws] = wdata
            continue
        for repo in repos:
            slug = repo.get("slug") if isinstance(repo, dict) else None
            if not slug:
                continue
            try:
                wdata["repositories"][str(slug)] = fn(ws, str(slug), access_token)
            except Exception as e:  # noqa: BLE001
                wdata["repositories"][str(slug)] = {"error": str(e)[:1200]}
        out["workspaces"][ws] = wdata
    return out


def _strategy_repositories(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    out: dict[str, Any] = {"workspaces": {}}
    for ws in workspace_slugs:
        try:
            repos = api_client.list_repositories(ws, access_token, max_repos=80)
            out["workspaces"][ws] = {
                "repository_count": len(repos),
                "repositories": [
                    {
                        "slug": r.get("slug"),
                        "name": r.get("name"),
                        "uuid": r.get("uuid"),
                        "is_private": r.get("is_private"),
                        "mainbranch": (r.get("mainbranch") or {}).get("name") if isinstance(r.get("mainbranch"), dict) else None,
                        "created_on": r.get("created_on"),
                        "updated_on": r.get("updated_on"),
                    }
                    for r in repos
                    if isinstance(r, dict)
                ],
            }
        except Exception as e:  # noqa: BLE001
            out["workspaces"][ws] = {"error": str(e)[:2000]}
    return out


def _strategy_commits(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {
            "recent_commits": api_client.list_commits(w, rs, tok, limit=25),
        },
    )


def _strategy_pull_requests(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    def pr_for_repo(w: str, rs: str, tok: str) -> dict[str, Any]:
        open_prs = api_client.list_pull_requests(w, rs, tok, state="OPEN", max_prs=40)
        merged = api_client.list_pull_requests(w, rs, tok, state="MERGED", max_prs=20)
        return {"open_pullrequests": open_prs, "merged_sample": merged}

    return _per_repo_bundle(workspace_slugs, access_token, fn=pr_for_repo)


def _strategy_pipelines(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {"pipeline_runs": api_client.list_pipeline_runs(w, rs, tok, max_runs=25)},
    )


def _strategy_deployments(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {"deployments": api_client.list_deployments(w, rs, tok, max_items=40)},
    )


def _strategy_hooks(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {"hooks": api_client.list_repo_hooks(w, rs, tok)},
    )


def _strategy_branch_restrictions(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {"branch_restrictions": api_client.list_branch_restrictions(w, rs, access_token)},
    )


def _strategy_issues(_code: str, workspace_slugs: list[str], access_token: str) -> dict[str, Any]:
    return _per_repo_bundle(
        workspace_slugs,
        access_token,
        fn=lambda w, rs, tok: {"issues": api_client.list_issues(w, rs, access_token, max_items=30)},
    )


_STRATEGY_FN = {
    "repositories": _strategy_repositories,
    "commits": _strategy_commits,
    "pull_requests": _strategy_pull_requests,
    "pipelines": _strategy_pipelines,
    "deployments": _strategy_deployments,
    "hooks": _strategy_hooks,
    "branch_restrictions": _strategy_branch_restrictions,
    "issues": _strategy_issues,
}


def collect_for_master(master: dict[str, Any], cfg: dict[str, Any], *, access_token: str) -> dict[str, Any]:
    code = str(master.get("code") or "").strip()
    slugs = _selected_slugs(cfg)
    if not slugs:
        raise ValueError("No workspaces selected; POST .../workspaces first.")

    strategy = EVIDENCE_CODE_STRATEGY.get(code, "not_applicable")
    if strategy == "not_applicable":
        return _not_applicable(code)

    fn = _STRATEGY_FN.get(strategy)
    if fn is None:
        return _not_applicable(code, reason=f"Unknown strategy {strategy!r}.")

    payload = fn(code, slugs, access_token)
    if isinstance(payload, dict):
        payload["evidence_code"] = code
        payload["integration"] = "bitbucket_cloud"
        payload["collectable_via_bitbucket_api"] = True
    return payload


def bitbucket_evidence_for_storage(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
