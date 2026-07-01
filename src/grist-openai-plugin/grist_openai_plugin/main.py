"""FastAPI server exposing Grist as a GPT Action (OpenAPI tool) for ChatGPT.

Run locally with:
    uvicorn grist_openai_plugin.main:app --reload

Then expose it over HTTPS (e.g. via a reverse proxy or tunnel) and point a
Custom GPT Action at "<public-url>/openapi.json".
"""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Query, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .client import GristAPIError, GristClient
from .models import (
    AddColumnsBody,
    AddRecordsBody,
    AddTablesBody,
    DeleteRecordsBody,
    NameBody,
    RunSqlBody,
    UpdateColumnsBody,
    UpdateRecordsBody,
)

load_dotenv()

app = FastAPI(
    title="Grist Action",
    description=(
        "Read and write Grist documents: organizations, workspaces, docs, "
        "tables, columns, records, and read-only SQL queries."
    ),
    version="0.1.0",
)

_bearer = HTTPBearer(auto_error=False)
_client: GristClient | None = None


def _get_client() -> GristClient:
    global _client
    if _client is None:
        _client = GristClient()
    return _client


def _check_auth(
    creds: HTTPAuthorizationCredentials | None = Security(_bearer),
) -> None:
    """Verify the caller's bearer token against ACTION_API_KEY.

    If ACTION_API_KEY is unset, auth is skipped (local development only —
    always set it before exposing this server publicly).
    """
    expected = os.environ.get("ACTION_API_KEY")
    if not expected:
        return
    if creds is None or creds.credentials != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing bearer token")


def _call(fn, *args: Any, **kwargs: Any) -> Any:
    try:
        return fn(*args, **kwargs)
    except GristAPIError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e


# --- Orgs -------------------------------------------------------------------


@app.get("/orgs", operation_id="listOrgs", summary="List Grist organizations")
def list_orgs(_: None = Depends(_check_auth)) -> Any:
    """List all Grist organizations accessible with the configured API key."""
    return _call(_get_client().list_orgs)


# --- Workspaces ---------------------------------------------------------------


@app.get(
    "/orgs/{org_id}/workspaces",
    operation_id="listWorkspaces",
    summary="List workspaces in an organization",
)
def list_workspaces(org_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_workspaces, org_id)


@app.get(
    "/workspaces/{workspace_id}",
    operation_id="getWorkspace",
    summary="Get a workspace, including the docs it contains",
)
def get_workspace(workspace_id: int, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().get_workspace, workspace_id)


@app.post(
    "/orgs/{org_id}/workspaces",
    operation_id="createWorkspace",
    summary="Create a new workspace in an organization",
)
def create_workspace(
    org_id: str, body: NameBody, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().create_workspace, org_id, body.name)


# --- Docs ---------------------------------------------------------------------


@app.post(
    "/workspaces/{workspace_id}/docs",
    operation_id="createDoc",
    summary="Create a new empty Grist document in a workspace",
)
def create_doc(
    workspace_id: int, body: NameBody, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().create_doc, workspace_id, body.name)


@app.get("/docs/{doc_id}", operation_id="getDoc", summary="Get document metadata")
def get_doc(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().get_doc, doc_id)


# --- Tables ---------------------------------------------------------------------


@app.get(
    "/docs/{doc_id}/tables",
    operation_id="listTables",
    summary="List the tables in a document",
)
def list_tables(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_tables, doc_id)


@app.post(
    "/docs/{doc_id}/tables",
    operation_id="addTables",
    summary="Create one or more new tables in a document",
)
def add_tables(
    doc_id: str, body: AddTablesBody, _: None = Depends(_check_auth)
) -> Any:
    tables = [t.model_dump() for t in body.tables]
    return _call(_get_client().add_tables, doc_id, tables)


# --- Columns ----------------------------------------------------------------------


@app.get(
    "/docs/{doc_id}/tables/{table_id}/columns",
    operation_id="listColumns",
    summary="List the columns of a table",
)
def list_columns(doc_id: str, table_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_columns, doc_id, table_id)


@app.post(
    "/docs/{doc_id}/tables/{table_id}/columns",
    operation_id="addColumns",
    summary="Add new columns to a table",
)
def add_columns(
    doc_id: str,
    table_id: str,
    body: AddColumnsBody,
    _: None = Depends(_check_auth),
) -> Any:
    columns = [c.model_dump() for c in body.columns]
    return _call(_get_client().add_columns, doc_id, table_id, columns)


@app.patch(
    "/docs/{doc_id}/tables/{table_id}/columns",
    operation_id="updateColumns",
    summary="Update properties of existing columns",
)
def update_columns(
    doc_id: str,
    table_id: str,
    body: UpdateColumnsBody,
    _: None = Depends(_check_auth),
) -> Any:
    columns = [c.model_dump() for c in body.columns]
    return _call(_get_client().update_columns, doc_id, table_id, columns)


# --- Records ------------------------------------------------------------------------


@app.get(
    "/docs/{doc_id}/tables/{table_id}/records",
    operation_id="listRecords",
    summary="List records from a table",
)
def list_records(
    doc_id: str,
    table_id: str,
    filter: str | None = Query(
        default=None,
        description=(
            'JSON-encoded column filter, e.g. {"Status": ["Done"]} matches rows '
            "where Status equals \"Done\"."
        ),
    ),
    sort: str | None = Query(
        default=None,
        description='Comma-separated sort spec, e.g. "-CreatedAt,Name" ("-" = descending).',
    ),
    limit: int | None = Query(default=None, description="Maximum number of records to return"),
    _: None = Depends(_check_auth),
) -> Any:
    import json

    filter_dict = json.loads(filter) if filter else None
    return _call(_get_client().list_records, doc_id, table_id, filter_dict, sort, limit)


@app.post(
    "/docs/{doc_id}/tables/{table_id}/records",
    operation_id="addRecords",
    summary="Add new records to a table",
)
def add_records(
    doc_id: str,
    table_id: str,
    body: AddRecordsBody,
    _: None = Depends(_check_auth),
) -> Any:
    records = [r.model_dump() for r in body.records]
    return _call(_get_client().add_records, doc_id, table_id, records)


@app.patch(
    "/docs/{doc_id}/tables/{table_id}/records",
    operation_id="updateRecords",
    summary="Update existing records by row ID",
)
def update_records(
    doc_id: str,
    table_id: str,
    body: UpdateRecordsBody,
    _: None = Depends(_check_auth),
) -> Any:
    records = [r.model_dump() for r in body.records]
    return _call(_get_client().update_records, doc_id, table_id, records)


@app.post(
    "/docs/{doc_id}/tables/{table_id}/records/delete",
    operation_id="deleteRecords",
    summary="Delete records from a table by row ID",
)
def delete_records(
    doc_id: str,
    table_id: str,
    body: DeleteRecordsBody,
    _: None = Depends(_check_auth),
) -> Any:
    return _call(_get_client().delete_records, doc_id, table_id, body.record_ids)


# --- SQL --------------------------------------------------------------------------


@app.post(
    "/docs/{doc_id}/sql",
    operation_id="runSql",
    summary="Run a read-only SQL SELECT query against a document",
)
def run_sql(doc_id: str, body: RunSqlBody, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().run_sql, doc_id, body.sql, body.args)


def main() -> None:
    import uvicorn

    uvicorn.run(
        "grist_openai_plugin.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
    )


if __name__ == "__main__":
    main()
