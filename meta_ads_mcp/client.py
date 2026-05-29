"""HTTP client wrapper for the Meta Graph (Marketing) API."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()


class MetaConfigError(RuntimeError):
    """Raised when required environment configuration is missing."""


class MetaAPIError(RuntimeError):
    """Raised when the Meta Graph API returns a non-success response."""

    def __init__(self, status_code: int, payload: Any) -> None:
        self.status_code = status_code
        self.payload = payload
        if isinstance(payload, dict):
            err = payload.get("error", {})
            message = err.get("message") or err.get("error_user_msg") or str(payload)
        else:
            message = str(payload)
        super().__init__(f"Meta API error {status_code}: {message}")


def _graph_version() -> str:
    return os.environ.get("META_GRAPH_API_VERSION", "v21.0")


def _graph_base() -> str:
    return f"https://graph.facebook.com/{_graph_version()}"


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise MetaConfigError(
            f"{name} is not set. Configure it in your environment or .env file."
        )
    return value


def access_token() -> str:
    return _require_env("META_ACCESS_TOKEN")


def ad_account_id() -> str:
    raw = _require_env("META_AD_ACCOUNT_ID")
    return raw if raw.startswith("act_") else f"act_{raw}"


def page_id() -> str:
    return _require_env("META_PAGE_ID")


def _raise_for_status(resp: httpx.Response) -> None:
    if resp.status_code >= 400:
        try:
            payload: Any = resp.json()
        except Exception:
            payload = resp.text
        raise MetaAPIError(resp.status_code, payload)


def get(path: str, params: dict | None = None) -> dict:
    p = dict(params or {})
    p["access_token"] = access_token()
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(f"{_graph_base()}/{path.lstrip('/')}", params=p)
    _raise_for_status(resp)
    return resp.json()


def post(
    path: str,
    data: dict | None = None,
    files: dict | None = None,
) -> dict:
    payload = {k: v for k, v in (data or {}).items() if v is not None}
    payload["access_token"] = access_token()
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(
            f"{_graph_base()}/{path.lstrip('/')}",
            data=payload,
            files=files,
        )
    _raise_for_status(resp)
    return resp.json()


def delete(path: str, params: dict | None = None) -> dict:
    p = dict(params or {})
    p["access_token"] = access_token()
    with httpx.Client(timeout=30.0) as client:
        resp = client.delete(f"{_graph_base()}/{path.lstrip('/')}", params=p)
    _raise_for_status(resp)
    return resp.json()


def paginate(path: str, params: dict | None = None, limit: int | None = None) -> list[dict]:
    """Follow Graph API cursor pagination and return up to `limit` items."""
    items: list[dict] = []
    page = get(path, params)
    items.extend(page.get("data", []))
    next_url = page.get("paging", {}).get("next")
    while next_url and (limit is None or len(items) < limit):
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(next_url)
        _raise_for_status(resp)
        page = resp.json()
        items.extend(page.get("data", []))
        next_url = page.get("paging", {}).get("next")
    if limit is not None:
        items = items[:limit]
    return items


def upload_image_multipart(file_path: str | Path, field_name: str | None = None) -> dict:
    """Upload an image file via multipart to /act_{id}/adimages.

    Returns the raw response payload — caller extracts the hash.
    """
    path = Path(file_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {path}")
    name = field_name or path.stem
    with path.open("rb") as fh:
        files = {name: (path.name, fh.read())}
    return post(f"{ad_account_id()}/adimages", files=files)
