"""Thin wrapper around the Grist REST API.

Reference: https://support.getgrist.com/api/
"""

from __future__ import annotations

import os
from typing import Any

import requests


class GristAPIError(RuntimeError):
    """Raised when the Grist API returns a non-2xx response."""

    def __init__(self, status_code: int, message: str):
        super().__init__(f"Grist API error {status_code}: {message}")
        self.status_code = status_code


class GristClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ.get("GRIST_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Missing Grist API key. Set GRIST_API_KEY in the environment."
            )
        self.base_url = (
            base_url or os.environ.get("GRIST_API_URL") or "https://docs.getgrist.com/api"
        ).rstrip("/")
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        resp = self._session.request(method, url, timeout=30, **kwargs)
        if not resp.ok:
            detail = resp.text
            try:
                detail = resp.json().get("error", detail)
            except ValueError:
                pass
            raise GristAPIError(resp.status_code, detail)
        if not resp.content:
            return None
        return resp.json()

    # --- Orgs ---------------------------------------------------------

    def list_orgs(self) -> Any:
        return self._request("GET", "/orgs")

    # --- Workspaces -----------------------------------------------------

    def list_workspaces(self, org_id: str) -> Any:
        return self._request("GET", f"/orgs/{org_id}/workspaces")

    def get_workspace(self, workspace_id: int) -> Any:
        return self._request("GET", f"/workspaces/{workspace_id}")

    def create_workspace(self, org_id: str, name: str) -> Any:
        return self._request(
            "POST", f"/orgs/{org_id}/workspaces", json={"name": name}
        )

    # --- Docs -----------------------------------------------------------

    def create_doc(self, workspace_id: int, name: str) -> Any:
        return self._request(
            "POST", f"/workspaces/{workspace_id}/docs", json={"name": name}
        )

    def get_doc(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}")

    # --- Tables -----------------------------------------------------------

    def list_tables(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/tables")

    def add_tables(self, doc_id: str, tables: list[dict[str, Any]]) -> Any:
        return self._request(
            "POST", f"/docs/{doc_id}/tables", json={"tables": tables}
        )

    # --- Columns ------------------------------------------------------------

    def list_columns(self, doc_id: str, table_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/tables/{table_id}/columns")

    def add_columns(
        self, doc_id: str, table_id: str, columns: list[dict[str, Any]]
    ) -> Any:
        return self._request(
            "POST",
            f"/docs/{doc_id}/tables/{table_id}/columns",
            json={"columns": columns},
        )

    def update_columns(
        self, doc_id: str, table_id: str, columns: list[dict[str, Any]]
    ) -> Any:
        return self._request(
            "PATCH",
            f"/docs/{doc_id}/tables/{table_id}/columns",
            json={"columns": columns},
        )

    # --- Records --------------------------------------------------------------

    def list_records(
        self,
        doc_id: str,
        table_id: str,
        filter: dict[str, list[Any]] | None = None,
        sort: str | None = None,
        limit: int | None = None,
    ) -> Any:
        params: dict[str, Any] = {}
        if filter:
            import json as _json

            params["filter"] = _json.dumps(filter)
        if sort:
            params["sort"] = sort
        if limit:
            params["limit"] = limit
        return self._request(
            "GET", f"/docs/{doc_id}/tables/{table_id}/records", params=params
        )

    def add_records(
        self, doc_id: str, table_id: str, records: list[dict[str, Any]]
    ) -> Any:
        return self._request(
            "POST",
            f"/docs/{doc_id}/tables/{table_id}/records",
            json={"records": records},
        )

    def update_records(
        self, doc_id: str, table_id: str, records: list[dict[str, Any]]
    ) -> Any:
        return self._request(
            "PATCH",
            f"/docs/{doc_id}/tables/{table_id}/records",
            json={"records": records},
        )

    def delete_records(
        self, doc_id: str, table_id: str, record_ids: list[int]
    ) -> Any:
        return self._request(
            "POST",
            f"/docs/{doc_id}/tables/{table_id}/data/delete",
            json=record_ids,
        )

    # --- SQL --------------------------------------------------------------

    def run_sql(
        self, doc_id: str, sql: str, args: list[Any] | None = None
    ) -> Any:
        """Read-only SQL query against the doc (SELECT only)."""
        body: dict[str, Any] = {"sql": sql}
        if args:
            body["args"] = args
        return self._request("POST", f"/docs/{doc_id}/sql", json=body)
