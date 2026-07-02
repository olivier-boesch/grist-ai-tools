"""MCP server exposing Grist as a set of tools for Claude (and other MCP clients)."""

from __future__ import annotations

import base64
from typing import Any

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import GristAPIError, GristClient

load_dotenv()

mcp = FastMCP("grist-mcp-server")
_client: GristClient | None = None


def _get_client() -> GristClient:
    global _client
    if _client is None:
        _client = GristClient()
    return _client


def _call(fn, *args, **kwargs) -> Any:
    try:
        return fn(*args, **kwargs)
    except GristAPIError as e:
        return {"error": str(e), "status_code": e.status_code}


def _call_webhook(fn, *args, **kwargs) -> Any:
    """Like _call, but clarifies the Grist instance's webhook URL allow-list 403.

    Grist rejects webhook URLs whose domain isn't in the server's
    ALLOWED_WEBHOOK_DOMAINS configuration, regardless of the URL's validity.
    The raw message ("Provided url is forbidden") reads like a client mistake,
    so we surface the real cause instead.
    """
    try:
        return fn(*args, **kwargs)
    except GristAPIError as e:
        if e.status_code == 403 and "forbidden" in str(e).lower():
            return {
                "error": (
                    "URL refusée par la politique de sécurité de l'instance Grist "
                    "(liste blanche de domaines pour les webhooks, ALLOWED_WEBHOOK_DOMAINS "
                    "côté serveur). Ce n'est pas une erreur de syntaxe de l'appel : "
                    "demandez à l'administrateur de l'instance d'autoriser ce domaine, "
                    "ou utilisez une URL sur un domaine déjà autorisé."
                ),
                "status_code": 403,
            }
        return {"error": str(e), "status_code": e.status_code}


# --- Orgs -----------------------------------------------------------------


@mcp.tool()
def list_orgs() -> Any:
    """List all Grist organizations accessible with the configured API key."""
    return _call(_get_client().list_orgs)


@mcp.tool()
def update_org(org_id: str, name: str) -> Any:
    """Rename an organization.

    Args:
        org_id: Organization ID or domain.
        name: New display name.
    """
    return _call(_get_client().update_org, org_id, name)


@mcp.tool()
def delete_org(org_id: str) -> Any:
    """Delete an organization. This is irreversible.

    Args:
        org_id: Organization ID or domain.
    """
    return _call(_get_client().delete_org, org_id)


@mcp.tool()
def list_org_access(org_id: str) -> Any:
    """List users and their access levels for an organization.

    Args:
        org_id: Organization ID or domain.
    """
    return _call(_get_client().list_org_access, org_id)


@mcp.tool()
def update_org_access(org_id: str, users: dict[str, str | None]) -> Any:
    """Change access levels for users on an organization.

    Args:
        org_id: Organization ID or domain.
        users: Map of email to role ("owners", "editors", "viewers"), or null
            to remove access, e.g. {"a@example.com": "editors"}.
    """
    return _call(_get_client().update_org_access, org_id, users)


# --- Workspaces -------------------------------------------------------------


@mcp.tool()
def list_workspaces(org_id: str) -> Any:
    """List workspaces in a Grist organization.

    Args:
        org_id: Organization ID or domain, as returned by list_orgs.
    """
    return _call(_get_client().list_workspaces, org_id)


@mcp.tool()
def get_workspace(workspace_id: int) -> Any:
    """Get details of a workspace, including the docs it contains.

    Args:
        workspace_id: Workspace ID, as returned by list_workspaces.
    """
    return _call(_get_client().get_workspace, workspace_id)


@mcp.tool()
def create_workspace(org_id: str, name: str) -> Any:
    """Create a new workspace inside an organization.

    Args:
        org_id: Organization ID or domain.
        name: Name of the new workspace.
    """
    return _call(_get_client().create_workspace, org_id, name)


@mcp.tool()
def update_workspace(workspace_id: int, name: str) -> Any:
    """Rename a workspace.

    Args:
        workspace_id: Workspace ID.
        name: New display name.
    """
    return _call(_get_client().update_workspace, workspace_id, name)


@mcp.tool()
def delete_workspace(workspace_id: int) -> Any:
    """Delete a workspace and all documents it contains. This is irreversible.

    Args:
        workspace_id: Workspace ID.
    """
    return _call(_get_client().delete_workspace, workspace_id)


@mcp.tool()
def list_workspace_access(workspace_id: int) -> Any:
    """List users and their access levels for a workspace.

    Args:
        workspace_id: Workspace ID.
    """
    return _call(_get_client().list_workspace_access, workspace_id)


@mcp.tool()
def update_workspace_access(workspace_id: int, users: dict[str, str | None]) -> Any:
    """Change access levels for users on a workspace.

    Args:
        workspace_id: Workspace ID.
        users: Map of email to role ("owners", "editors", "viewers"), or null
            to remove access.
    """
    return _call(_get_client().update_workspace_access, workspace_id, users)


# --- Docs -------------------------------------------------------------------


@mcp.tool()
def create_doc(workspace_id: int, name: str) -> Any:
    """Create a new (empty) Grist document inside a workspace.

    Args:
        workspace_id: Workspace ID to create the document in.
        name: Name of the new document.
    """
    return _call(_get_client().create_doc, workspace_id, name)


@mcp.tool()
def get_doc(doc_id: str) -> Any:
    """Get metadata for a Grist document.

    Args:
        doc_id: Document ID (the ID found in the doc's URL).
    """
    return _call(_get_client().get_doc, doc_id)


@mcp.tool()
def update_doc(doc_id: str, name: str) -> Any:
    """Rename a document.

    Args:
        doc_id: Document ID.
        name: New display name.
    """
    return _call(_get_client().update_doc, doc_id, name)


@mcp.tool()
def delete_doc(doc_id: str) -> Any:
    """Delete a document. This is irreversible.

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().delete_doc, doc_id)


@mcp.tool()
def move_doc(doc_id: str, workspace_id: int) -> Any:
    """Move a document to a different workspace.

    Args:
        doc_id: Document ID.
        workspace_id: Destination workspace ID.
    """
    return _call(_get_client().move_doc, doc_id, workspace_id)


@mcp.tool()
def download_doc(doc_id: str, nohistory: bool = False, template: bool = False) -> Any:
    """Download the full document as a base64-encoded SQLite file.

    Args:
        doc_id: Document ID.
        nohistory: If true, strip document history to reduce size.
        template: If true, strip data and history, keeping only structure.
    """
    try:
        content = _get_client().download_doc(doc_id, nohistory, template)
        return {"filename": f"{doc_id}.grist", "content_base64": base64.b64encode(content).decode()}
    except GristAPIError as e:
        return {"error": str(e), "status_code": e.status_code}


@mcp.tool()
def download_doc_xlsx(doc_id: str) -> Any:
    """Download the document as a base64-encoded XLSX file.

    Args:
        doc_id: Document ID.
    """
    try:
        content = _get_client().download_doc_xlsx(doc_id)
        return {"filename": f"{doc_id}.xlsx", "content_base64": base64.b64encode(content).decode()}
    except GristAPIError as e:
        return {"error": str(e), "status_code": e.status_code}


@mcp.tool()
def download_table_csv(doc_id: str, table_id: str) -> Any:
    """Download a single table as CSV text.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
    """
    try:
        content = _get_client().download_table_csv(doc_id, table_id)
        return {"filename": f"{table_id}.csv", "content": content.decode("utf-8")}
    except GristAPIError as e:
        return {"error": str(e), "status_code": e.status_code}


@mcp.tool()
def force_reload_doc(doc_id: str) -> Any:
    """Force the document to reload from storage, discarding in-memory state.

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().force_reload_doc, doc_id)


@mcp.tool()
def delete_doc_history(doc_id: str, keep: int) -> Any:
    """Truncate a document's undo history, keeping only the most recent states.

    Args:
        doc_id: Document ID.
        keep: Number of most recent history states to keep.
    """
    return _call(_get_client().delete_doc_history, doc_id, keep)


@mcp.tool()
def list_doc_access(doc_id: str) -> Any:
    """List users and their access levels for a document.

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().list_doc_access, doc_id)


@mcp.tool()
def update_doc_access(doc_id: str, users: dict[str, str | None]) -> Any:
    """Change access levels for users on a document.

    Args:
        doc_id: Document ID.
        users: Map of email to role ("owners", "editors", "viewers"), or null
            to remove access.
    """
    return _call(_get_client().update_doc_access, doc_id, users)


@mcp.tool()
def list_doc_users_for_view_as(doc_id: str) -> Any:
    """List users that can be impersonated for access-control preview ("view as").

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().list_doc_users_for_view_as, doc_id)


# --- Tables -------------------------------------------------------------------


@mcp.tool()
def list_tables(doc_id: str) -> Any:
    """List the tables in a Grist document.

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().list_tables, doc_id)


@mcp.tool()
def add_tables(doc_id: str, tables: list[dict[str, Any]]) -> Any:
    """Create one or more new tables in a document.

    Args:
        doc_id: Document ID.
        tables: List of table definitions, e.g.
            [{"id": "Tasks", "columns": [{"id": "Title", "fields": {"type": "Text"}}]}]
    """
    return _call(_get_client().add_tables, doc_id, tables)


@mcp.tool()
def update_tables(doc_id: str, tables: list[dict[str, Any]]) -> Any:
    """Update properties of existing tables (e.g. rename via the "tableId" field).

    Args:
        doc_id: Document ID.
        tables: List of table updates, e.g. [{"id": "Tasks", "fields": {"tableId": "MyTasks"}}]
    """
    return _call(_get_client().update_tables, doc_id, tables)


# --- Columns ------------------------------------------------------------------


@mcp.tool()
def list_columns(doc_id: str, table_id: str) -> Any:
    """List the columns of a table, including their types and options.

    Args:
        doc_id: Document ID.
        table_id: Table ID (as returned by list_tables).
    """
    return _call(_get_client().list_columns, doc_id, table_id)


@mcp.tool()
def add_columns(doc_id: str, table_id: str, columns: list[dict[str, Any]]) -> Any:
    """Add new columns to an existing table.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        columns: List of column definitions, e.g.
            [{"id": "DueDate", "fields": {"type": "Date", "label": "Due date"}}]
    """
    return _call(_get_client().add_columns, doc_id, table_id, columns)


@mcp.tool()
def update_columns(doc_id: str, table_id: str, columns: list[dict[str, Any]]) -> Any:
    """Update properties (type, label, formula, etc.) of existing columns.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        columns: List of column updates, e.g.
            [{"id": "DueDate", "fields": {"label": "Deadline"}}]
    """
    return _call(_get_client().update_columns, doc_id, table_id, columns)


@mcp.tool()
def delete_column(doc_id: str, table_id: str, column_id: str) -> Any:
    """Delete a single column from a table.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        column_id: Column ID to delete.
    """
    return _call(_get_client().delete_column, doc_id, table_id, column_id)


# --- Records --------------------------------------------------------------------


@mcp.tool()
def list_records(
    doc_id: str,
    table_id: str,
    filter: dict[str, list[Any]] | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> Any:
    """List records from a table, with optional filtering, sorting, and limiting.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        filter: Optional column filter, e.g. {"Status": ["Done"]} matches rows
            where the Status column equals "Done".
        sort: Optional comma-separated sort spec, e.g. "-CreatedAt,Name" (prefix
            a column with "-" for descending order).
        limit: Optional maximum number of records to return.
    """
    return _call(_get_client().list_records, doc_id, table_id, filter, sort, limit)


@mcp.tool()
def add_records(doc_id: str, table_id: str, records: list[dict[str, Any]]) -> Any:
    """Add new records (rows) to a table.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        records: List of records to add, e.g.
            [{"fields": {"Title": "Buy milk", "Done": False}}]
    """
    return _call(_get_client().add_records, doc_id, table_id, records)


@mcp.tool()
def update_records(doc_id: str, table_id: str, records: list[dict[str, Any]]) -> Any:
    """Update existing records by row ID.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        records: List of records to update, e.g.
            [{"id": 12, "fields": {"Done": True}}]
    """
    return _call(_get_client().update_records, doc_id, table_id, records)


@mcp.tool()
def delete_records(doc_id: str, table_id: str, record_ids: list[int]) -> Any:
    """Delete records from a table by row ID.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        record_ids: List of row IDs to delete, e.g. [12, 13].
    """
    return _call(_get_client().delete_records, doc_id, table_id, record_ids)


@mcp.tool()
def upsert_records(
    doc_id: str,
    table_id: str,
    records: list[dict[str, Any]],
    add: bool = True,
    update: bool = True,
    on_many: str = "first",
) -> Any:
    """Add or update records, matching existing rows by the given "require" fields.

    Args:
        doc_id: Document ID.
        table_id: Table ID.
        records: List of records, e.g.
            [{"require": {"Email": "a@b.com"}, "fields": {"Name": "A"}}]
            "require" selects the matching row(s); "fields" are the values to set
            (used both to create a new row if no match is found, and to update a
            matched row).
        add: If false, never create new rows (only update matches).
        update: If false, never update existing rows (only create new ones).
        on_many: Behavior when multiple rows match "require": "first" (default),
            "none" (skip), or "all" (update every match).
    """
    return _call(
        _get_client().upsert_records, doc_id, table_id, records, add, update, on_many
    )


# --- Attachments ------------------------------------------------------------------


@mcp.tool()
def list_attachments(
    doc_id: str,
    filter: dict[str, list[Any]] | None = None,
    sort: str | None = None,
    limit: int | None = None,
) -> Any:
    """List attachment metadata for a document.

    Args:
        doc_id: Document ID.
        filter: Optional column filter, same format as list_records.
        sort: Optional comma-separated sort spec.
        limit: Optional maximum number of results.
    """
    return _call(_get_client().list_attachments, doc_id, filter, sort, limit)


@mcp.tool()
def upload_attachments(doc_id: str, files: list[dict[str, str]]) -> Any:
    """Upload files as attachments to a document; returns their new IDs.

    Args:
        doc_id: Document ID.
        files: List of files to upload, each as
            {"filename": "photo.jpg", "content_base64": "<base64-encoded bytes>"}.
            The file content must be base64-encoded and passed inline: this MCP
            server has no access to the calling client's local filesystem.
    """
    return _call(_get_client().upload_attachments, doc_id, files)


@mcp.tool()
def get_attachment_metadata(doc_id: str, attachment_id: int) -> Any:
    """Get metadata (filename, size, timestamps) for an attachment.

    Args:
        doc_id: Document ID.
        attachment_id: Attachment ID.
    """
    return _call(_get_client().get_attachment_metadata, doc_id, attachment_id)


@mcp.tool()
def download_attachment(doc_id: str, attachment_id: int) -> Any:
    """Download an attachment's file content, base64-encoded.

    Args:
        doc_id: Document ID.
        attachment_id: Attachment ID.
    """
    try:
        content = _get_client().download_attachment(doc_id, attachment_id)
        return {"content_base64": base64.b64encode(content).decode()}
    except GristAPIError as e:
        return {"error": str(e), "status_code": e.status_code}


# --- Webhooks ---------------------------------------------------------------------


@mcp.tool()
def list_webhooks(doc_id: str) -> Any:
    """List webhooks configured on a document.

    Args:
        doc_id: Document ID.
    """
    return _call(_get_client().list_webhooks, doc_id)


@mcp.tool()
def create_webhook(doc_id: str, fields: dict[str, Any]) -> Any:
    """Create a webhook that notifies a URL of record changes.

    Args:
        doc_id: Document ID.
        fields: Webhook definition, e.g. {"url": "https://...", "eventTypes":
            ["add", "update"], "tableId": "Tasks", "enabled": true}
    """
    return _call_webhook(_get_client().create_webhook, doc_id, {"fields": fields})


@mcp.tool()
def update_webhook(doc_id: str, webhook_id: str, fields: dict[str, Any]) -> Any:
    """Update an existing webhook's configuration.

    Args:
        doc_id: Document ID.
        webhook_id: Webhook ID, as returned by list_webhooks.
        fields: Fields to update, e.g. {"enabled": false}.
    """
    return _call_webhook(_get_client().update_webhook, doc_id, webhook_id, fields)


@mcp.tool()
def delete_webhook(doc_id: str, webhook_id: str) -> Any:
    """Delete a webhook.

    Args:
        doc_id: Document ID.
        webhook_id: Webhook ID.
    """
    return _call(_get_client().delete_webhook, doc_id, webhook_id)


# --- SQL ------------------------------------------------------------------------


@mcp.tool()
def run_sql(doc_id: str, sql: str, args: list[Any] | None = None) -> Any:
    """Run a read-only SQL SELECT query against a document's tables.

    Table names in SQL match the table IDs from list_tables. Use "?" placeholders
    in the SQL and pass values via `args` rather than interpolating them directly.

    Args:
        doc_id: Document ID.
        sql: SQL SELECT statement.
        args: Optional list of parameter values for "?" placeholders in sql.
    """
    return _call(_get_client().run_sql, doc_id, sql, args)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
