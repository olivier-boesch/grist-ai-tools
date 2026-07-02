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

    def _request_binary(self, method: str, path: str, **kwargs: Any) -> bytes:
        url = f"{self.base_url}{path}"
        resp = self._session.request(method, url, timeout=60, **kwargs)
        if not resp.ok:
            detail = resp.text
            try:
                detail = resp.json().get("error", detail)
            except ValueError:
                pass
            raise GristAPIError(resp.status_code, detail)
        return resp.content

    # --- Orgs ---------------------------------------------------------

    def list_orgs(self) -> Any:
        return self._request("GET", "/orgs")

    def update_org(self, org_id: str, name: str) -> Any:
        return self._request("PATCH", f"/orgs/{org_id}", json={"name": name})

    def delete_org(self, org_id: str) -> Any:
        return self._request("DELETE", f"/orgs/{org_id}")

    def list_org_access(self, org_id: str) -> Any:
        return self._request("GET", f"/orgs/{org_id}/access")

    def update_org_access(self, org_id: str, users: dict[str, str | None]) -> Any:
        """users: {"user@example.com": "owners"|"editors"|"viewers"|None (None removes access)}"""
        return self._request(
            "PATCH", f"/orgs/{org_id}/access", json={"delta": {"users": users}}
        )

    # --- Workspaces -----------------------------------------------------

    def list_workspaces(self, org_id: str) -> Any:
        return self._request("GET", f"/orgs/{org_id}/workspaces")

    def get_workspace(self, workspace_id: int) -> Any:
        return self._request("GET", f"/workspaces/{workspace_id}")

    def create_workspace(self, org_id: str, name: str) -> Any:
        return self._request(
            "POST", f"/orgs/{org_id}/workspaces", json={"name": name}
        )

    def update_workspace(self, workspace_id: int, name: str) -> Any:
        return self._request(
            "PATCH", f"/workspaces/{workspace_id}", json={"name": name}
        )

    def delete_workspace(self, workspace_id: int) -> Any:
        return self._request("DELETE", f"/workspaces/{workspace_id}")

    def list_workspace_access(self, workspace_id: int) -> Any:
        return self._request("GET", f"/workspaces/{workspace_id}/access")

    def update_workspace_access(
        self, workspace_id: int, users: dict[str, str | None]
    ) -> Any:
        return self._request(
            "PATCH",
            f"/workspaces/{workspace_id}/access",
            json={"delta": {"users": users}},
        )

    # --- Docs -----------------------------------------------------------

    def create_doc(self, workspace_id: int, name: str) -> Any:
        return self._request(
            "POST", f"/workspaces/{workspace_id}/docs", json={"name": name}
        )

    def get_doc(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}")

    def update_doc(self, doc_id: str, name: str) -> Any:
        return self._request("PATCH", f"/docs/{doc_id}", json={"name": name})

    def delete_doc(self, doc_id: str) -> Any:
        return self._request("DELETE", f"/docs/{doc_id}")

    def move_doc(self, doc_id: str, workspace_id: int) -> Any:
        return self._request(
            "PATCH", f"/docs/{doc_id}/move", json={"workspace": workspace_id}
        )

    def download_doc(self, doc_id: str, nohistory: bool = False, template: bool = False) -> bytes:
        """Full document as a SQLite file (raw bytes)."""
        params = {"nohistory": str(nohistory).lower(), "template": str(template).lower()}
        return self._request_binary("GET", f"/docs/{doc_id}/download", params=params)

    def download_doc_xlsx(self, doc_id: str) -> bytes:
        return self._request_binary("GET", f"/docs/{doc_id}/download/xlsx")

    def download_table_csv(self, doc_id: str, table_id: str) -> bytes:
        return self._request_binary(
            "GET", f"/docs/{doc_id}/download/csv", params={"tableId": table_id}
        )

    def force_reload_doc(self, doc_id: str) -> Any:
        return self._request("POST", f"/docs/{doc_id}/force-reload")

    def delete_doc_history(self, doc_id: str, keep: int) -> Any:
        """Truncate document history, keeping the `keep` most recent states."""
        return self._request(
            "POST", f"/docs/{doc_id}/states/remove", json={"keep": keep}
        )

    def list_doc_access(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/access")

    def update_doc_access(self, doc_id: str, users: dict[str, str | None]) -> Any:
        return self._request(
            "PATCH", f"/docs/{doc_id}/access", json={"delta": {"users": users}}
        )

    def list_doc_users_for_view_as(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/usersForViewAs")

    # --- Tables -----------------------------------------------------------

    def list_tables(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/tables")

    def add_tables(self, doc_id: str, tables: list[dict[str, Any]]) -> Any:
        return self._request(
            "POST", f"/docs/{doc_id}/tables", json={"tables": tables}
        )

    def update_tables(self, doc_id: str, tables: list[dict[str, Any]]) -> Any:
        return self._request(
            "PATCH", f"/docs/{doc_id}/tables", json={"tables": tables}
        )

    # --- Columns ------------------------------------------------------------

    def list_columns(self, doc_id: str, table_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/tables/{table_id}/columns")

    def add_columns(
        self, doc_id: str, table_id: str, columns: list[dict[str, Any]]
    ) -> Any:
        """Grist defaults a new column to isFormula=True when "formula" isn't
        set, which is rarely what's intended for a plain data column. If the
        caller didn't specify "formula" or "isFormula", default to a regular
        (non-formula) column.
        """
        for column in columns:
            fields = column.setdefault("fields", {})
            if "formula" not in fields and "isFormula" not in fields:
                fields["isFormula"] = False
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

    def delete_column(self, doc_id: str, table_id: str, column_id: str) -> Any:
        return self._request(
            "DELETE", f"/docs/{doc_id}/tables/{table_id}/columns/{column_id}"
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

    def upsert_records(
        self,
        doc_id: str,
        table_id: str,
        records: list[dict[str, Any]],
        add: bool = True,
        update: bool = True,
        on_many: str = "first",
    ) -> Any:
        """Add-or-update records, matched by their `require` fields.

        records: [{"require": {"Email": "a@b.com"}, "fields": {"Name": "A"}}]
        on_many: "first" | "none" | "all" — behavior when multiple rows match.
        """
        params = {
            "onmany": on_many,
            "noadd": str(not add).lower(),
            "noupdate": str(not update).lower(),
        }
        return self._request(
            "PUT",
            f"/docs/{doc_id}/tables/{table_id}/records",
            params=params,
            json={"records": records},
        )

    # --- Attachments --------------------------------------------------------

    def list_attachments(
        self,
        doc_id: str,
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
        return self._request("GET", f"/docs/{doc_id}/attachments", params=params)

    def upload_attachments(self, doc_id: str, files: list[tuple[str, bytes]]) -> Any:
        """Upload attachments; files: [(filename, content_bytes), ...]."""
        upload_files = [("upload", (name, content)) for name, content in files]
        url = f"{self.base_url}/docs/{doc_id}/attachments"
        # The session sets a default "Content-Type: application/json" header,
        # which `requests` would otherwise keep verbatim on a multipart request
        # (explicit headers only override same-named session headers, they
        # don't remove them). Set it to None so requests drops it and computes
        # its own "multipart/form-data; boundary=..." — without this, Grist
        # can't parse the body and rejects it with "failed upload".
        headers = {k: v for k, v in self._session.headers.items() if k != "Content-Type"}
        headers["Content-Type"] = None
        resp = self._session.post(url, files=upload_files, headers=headers, timeout=60)
        if not resp.ok:
            detail = resp.text
            try:
                detail = resp.json().get("error", detail)
            except ValueError:
                pass
            raise GristAPIError(resp.status_code, detail)
        return resp.json()

    def get_attachment_metadata(self, doc_id: str, attachment_id: int) -> Any:
        return self._request("GET", f"/docs/{doc_id}/attachments/{attachment_id}")

    def download_attachment(self, doc_id: str, attachment_id: int) -> bytes:
        return self._request_binary(
            "GET", f"/docs/{doc_id}/attachments/{attachment_id}/download"
        )

    # --- Webhooks -------------------------------------------------------------

    def list_webhooks(self, doc_id: str) -> Any:
        return self._request("GET", f"/docs/{doc_id}/webhooks")

    def create_webhook(self, doc_id: str, webhook: dict[str, Any]) -> Any:
        """webhook: {"fields": {"url": ..., "eventTypes": ["add","update"], "tableId": ...}}"""
        return self._request(
            "POST", f"/docs/{doc_id}/webhooks", json={"webhooks": [webhook]}
        )

    def update_webhook(
        self, doc_id: str, webhook_id: str, fields: dict[str, Any]
    ) -> Any:
        return self._request(
            "PATCH",
            f"/docs/{doc_id}/webhooks/{webhook_id}",
            json={"webhook": {"fields": fields}},
        )

    def delete_webhook(self, doc_id: str, webhook_id: str) -> Any:
        return self._request("DELETE", f"/docs/{doc_id}/webhooks/{webhook_id}")

    # --- SQL --------------------------------------------------------------

    def run_sql(
        self, doc_id: str, sql: str, args: list[Any] | None = None
    ) -> Any:
        """Read-only SQL query against the doc (SELECT only)."""
        body: dict[str, Any] = {"sql": sql}
        if args:
            body["args"] = args
        return self._request("POST", f"/docs/{doc_id}/sql", json=body)
