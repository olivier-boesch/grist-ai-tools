"""MCP server exposing Grist as a set of tools for Claude (and other MCP clients)."""

from __future__ import annotations

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


# --- Orgs -----------------------------------------------------------------


@mcp.tool()
def list_orgs() -> Any:
    """List all Grist organizations accessible with the configured API key."""
    return _call(_get_client().list_orgs)


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
