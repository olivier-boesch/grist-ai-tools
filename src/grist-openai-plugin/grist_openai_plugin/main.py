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
from fastapi import Depends, FastAPI, File, HTTPException, Query, Security, UploadFile
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .client import GristAPIError, GristClient
from .models import (
    AccessDelta,
    AddColumnsBody,
    AddRecordsBody,
    AddTablesBody,
    CreateWebhookBody,
    DeleteHistoryBody,
    DeleteRecordsBody,
    MoveDocBody,
    NameBody,
    RunSqlBody,
    UpdateColumnsBody,
    UpdateRecordsBody,
    UpdateTablesBody,
    UpdateWebhookBody,
    UpsertRecordsBody,
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


@app.patch("/orgs/{org_id}", operation_id="updateOrg", summary="Rename an organization")
def update_org(org_id: str, body: NameBody, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().update_org, org_id, body.name)


@app.delete(
    "/orgs/{org_id}",
    operation_id="deleteOrg",
    summary="Delete an organization (irreversible)",
)
def delete_org(org_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().delete_org, org_id)


@app.get(
    "/orgs/{org_id}/access",
    operation_id="listOrgAccess",
    summary="List users and access levels for an organization",
)
def list_org_access(org_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_org_access, org_id)


@app.patch(
    "/orgs/{org_id}/access",
    operation_id="updateOrgAccess",
    summary="Change access levels for users on an organization",
)
def update_org_access(
    org_id: str, body: AccessDelta, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().update_org_access, org_id, body.users)


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


@app.patch(
    "/workspaces/{workspace_id}",
    operation_id="updateWorkspace",
    summary="Rename a workspace",
)
def update_workspace(
    workspace_id: int, body: NameBody, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().update_workspace, workspace_id, body.name)


@app.delete(
    "/workspaces/{workspace_id}",
    operation_id="deleteWorkspace",
    summary="Delete a workspace and its documents (irreversible)",
)
def delete_workspace(workspace_id: int, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().delete_workspace, workspace_id)


@app.get(
    "/workspaces/{workspace_id}/access",
    operation_id="listWorkspaceAccess",
    summary="List users and access levels for a workspace",
)
def list_workspace_access(workspace_id: int, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_workspace_access, workspace_id)


@app.patch(
    "/workspaces/{workspace_id}/access",
    operation_id="updateWorkspaceAccess",
    summary="Change access levels for users on a workspace",
)
def update_workspace_access(
    workspace_id: int, body: AccessDelta, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().update_workspace_access, workspace_id, body.users)


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


@app.patch("/docs/{doc_id}", operation_id="updateDoc", summary="Rename a document")
def update_doc(doc_id: str, body: NameBody, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().update_doc, doc_id, body.name)


@app.delete(
    "/docs/{doc_id}",
    operation_id="deleteDoc",
    summary="Delete a document (irreversible)",
)
def delete_doc(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().delete_doc, doc_id)


@app.post(
    "/docs/{doc_id}/move",
    operation_id="moveDoc",
    summary="Move a document to a different workspace",
)
def move_doc(doc_id: str, body: MoveDocBody, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().move_doc, doc_id, body.workspace_id)


@app.get(
    "/docs/{doc_id}/download",
    operation_id="downloadDoc",
    summary="Download the full document as a SQLite file",
)
def download_doc(
    doc_id: str,
    nohistory: bool = Query(default=False, description="Strip document history"),
    template: bool = Query(default=False, description="Strip data, keep only structure"),
    _: None = Depends(_check_auth),
) -> Response:
    content = _call(_get_client().download_doc, doc_id, nohistory, template)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/docs/{doc_id}/download/xlsx",
    operation_id="downloadDocXlsx",
    summary="Download the document as an XLSX file",
)
def download_doc_xlsx(doc_id: str, _: None = Depends(_check_auth)) -> Response:
    content = _call(_get_client().download_doc_xlsx, doc_id)
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get(
    "/docs/{doc_id}/download/csv",
    operation_id="downloadTableCsv",
    summary="Download a single table as CSV",
)
def download_table_csv(
    doc_id: str, table_id: str = Query(...), _: None = Depends(_check_auth)
) -> Response:
    content = _call(_get_client().download_table_csv, doc_id, table_id)
    return Response(content=content, media_type="text/csv")


@app.post(
    "/docs/{doc_id}/force-reload",
    operation_id="forceReloadDoc",
    summary="Force the document to reload from storage",
)
def force_reload_doc(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().force_reload_doc, doc_id)


@app.patch(
    "/docs/{doc_id}/states/remove",
    operation_id="deleteDocHistory",
    summary="Truncate document history, keeping the most recent states",
)
def delete_doc_history(
    doc_id: str, body: DeleteHistoryBody, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().delete_doc_history, doc_id, body.keep)


@app.get(
    "/docs/{doc_id}/access",
    operation_id="listDocAccess",
    summary="List users and access levels for a document",
)
def list_doc_access(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_doc_access, doc_id)


@app.patch(
    "/docs/{doc_id}/access",
    operation_id="updateDocAccess",
    summary="Change access levels for users on a document",
)
def update_doc_access(
    doc_id: str, body: AccessDelta, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().update_doc_access, doc_id, body.users)


@app.get(
    "/docs/{doc_id}/usersForViewAs",
    operation_id="listDocUsersForViewAs",
    summary='List users available for access-control preview ("view as")',
)
def list_doc_users_for_view_as(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_doc_users_for_view_as, doc_id)


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


@app.patch(
    "/docs/{doc_id}/tables",
    operation_id="updateTables",
    summary="Update properties of existing tables (e.g. rename)",
)
def update_tables(
    doc_id: str, body: UpdateTablesBody, _: None = Depends(_check_auth)
) -> Any:
    tables = [t.model_dump() for t in body.tables]
    return _call(_get_client().update_tables, doc_id, tables)


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


@app.delete(
    "/docs/{doc_id}/tables/{table_id}/columns/{column_id}",
    operation_id="deleteColumn",
    summary="Delete a single column from a table",
)
def delete_column(
    doc_id: str, table_id: str, column_id: str, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().delete_column, doc_id, table_id, column_id)


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


@app.put(
    "/docs/{doc_id}/tables/{table_id}/records",
    operation_id="upsertRecords",
    summary="Add or update records, matched by a set of key fields",
)
def upsert_records(
    doc_id: str,
    table_id: str,
    body: UpsertRecordsBody,
    _: None = Depends(_check_auth),
) -> Any:
    records = [r.model_dump() for r in body.records]
    return _call(
        _get_client().upsert_records,
        doc_id,
        table_id,
        records,
        body.add,
        body.update,
        body.on_many,
    )


# --- Attachments --------------------------------------------------------------------


@app.get(
    "/docs/{doc_id}/attachments",
    operation_id="listAttachments",
    summary="List attachment metadata for a document",
)
def list_attachments(
    doc_id: str,
    filter: str | None = Query(
        default=None, description="JSON-encoded column filter, same format as listRecords"
    ),
    sort: str | None = Query(default=None, description="Comma-separated sort spec"),
    limit: int | None = Query(default=None, description="Maximum number of results"),
    _: None = Depends(_check_auth),
) -> Any:
    import json

    filter_dict = json.loads(filter) if filter else None
    return _call(_get_client().list_attachments, doc_id, filter_dict, sort, limit)


@app.post(
    "/docs/{doc_id}/attachments",
    operation_id="uploadAttachments",
    summary="Upload one or more files as attachments",
)
async def upload_attachments(
    doc_id: str,
    upload: list[UploadFile] = File(...),
    _: None = Depends(_check_auth),
) -> Any:
    files = [(f.filename or "file", await f.read()) for f in upload]
    return _call(_get_client().upload_attachments, doc_id, files)


@app.get(
    "/docs/{doc_id}/attachments/{attachment_id}",
    operation_id="getAttachmentMetadata",
    summary="Get metadata for an attachment",
)
def get_attachment_metadata(
    doc_id: str, attachment_id: int, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().get_attachment_metadata, doc_id, attachment_id)


@app.get(
    "/docs/{doc_id}/attachments/{attachment_id}/download",
    operation_id="downloadAttachment",
    summary="Download an attachment's file content",
)
def download_attachment(
    doc_id: str, attachment_id: int, _: None = Depends(_check_auth)
) -> Response:
    content = _call(_get_client().download_attachment, doc_id, attachment_id)
    return Response(content=content, media_type="application/octet-stream")


# --- Webhooks -----------------------------------------------------------------------


@app.get(
    "/docs/{doc_id}/webhooks",
    operation_id="listWebhooks",
    summary="List webhooks configured on a document",
)
def list_webhooks(doc_id: str, _: None = Depends(_check_auth)) -> Any:
    return _call(_get_client().list_webhooks, doc_id)


@app.post(
    "/docs/{doc_id}/webhooks",
    operation_id="createWebhook",
    summary="Create a webhook that notifies a URL of record changes",
)
def create_webhook(
    doc_id: str, body: CreateWebhookBody, _: None = Depends(_check_auth)
) -> Any:
    webhook = {"fields": body.fields.model_dump(by_alias=True)}
    return _call(_get_client().create_webhook, doc_id, webhook)


@app.patch(
    "/docs/{doc_id}/webhooks/{webhook_id}",
    operation_id="updateWebhook",
    summary="Update an existing webhook's configuration",
)
def update_webhook(
    doc_id: str,
    webhook_id: str,
    body: UpdateWebhookBody,
    _: None = Depends(_check_auth),
) -> Any:
    return _call(_get_client().update_webhook, doc_id, webhook_id, body.fields)


@app.delete(
    "/docs/{doc_id}/webhooks/{webhook_id}",
    operation_id="deleteWebhook",
    summary="Delete a webhook",
)
def delete_webhook(
    doc_id: str, webhook_id: str, _: None = Depends(_check_auth)
) -> Any:
    return _call(_get_client().delete_webhook, doc_id, webhook_id)


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
