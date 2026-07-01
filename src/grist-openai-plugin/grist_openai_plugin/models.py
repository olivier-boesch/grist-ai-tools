"""Pydantic request/response models for the Grist GPT Action."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    status_code: int


class NameBody(BaseModel):
    name: str = Field(..., description="Display name")


class MoveDocBody(BaseModel):
    workspace_id: int = Field(..., description="Destination workspace ID")


class AccessDelta(BaseModel):
    users: dict[str, str | None] = Field(
        ...,
        description=(
            'Map of email to role ("owners", "editors", "viewers"), or null to '
            'remove access, e.g. {"a@example.com": "editors"}.'
        ),
    )


class DeleteHistoryBody(BaseModel):
    keep: int = Field(..., description="Number of most recent history states to keep")


class ColumnDef(BaseModel):
    id: str = Field(..., description="Column ID (stable identifier, e.g. 'DueDate')")
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Column properties, e.g. {\"type\": \"Text\", \"label\": \"Due date\"}. "
            "Common types: Text, Numeric, Int, Bool, Date, DateTime, Choice, Ref, RefList."
        ),
    )


class TableDef(BaseModel):
    id: str = Field(..., description="Table ID (stable identifier, e.g. 'Tasks')")
    columns: list[ColumnDef] = Field(default_factory=list)


class TableUpdate(BaseModel):
    id: str = Field(..., description="Table ID to update")
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Table properties to update, e.g. {\"tableId\": \"NewName\"}",
    )


class AddTablesBody(BaseModel):
    tables: list[TableDef]


class UpdateTablesBody(BaseModel):
    tables: list[TableUpdate]


class AddColumnsBody(BaseModel):
    columns: list[ColumnDef]


class UpdateColumnsBody(BaseModel):
    columns: list[ColumnDef]


class RecordCreate(BaseModel):
    fields: dict[str, Any] = Field(
        ..., description="Column values for the new record, e.g. {\"Title\": \"Buy milk\"}"
    )


class RecordUpdate(BaseModel):
    id: int = Field(..., description="Row ID of the record to update")
    fields: dict[str, Any] = Field(
        ..., description="Column values to update, e.g. {\"Done\": true}"
    )


class AddRecordsBody(BaseModel):
    records: list[RecordCreate]


class UpdateRecordsBody(BaseModel):
    records: list[RecordUpdate]


class DeleteRecordsBody(BaseModel):
    record_ids: list[int] = Field(..., description="Row IDs to delete")


class RecordUpsert(BaseModel):
    require: dict[str, Any] = Field(
        ..., description="Column values that identify the row to match, e.g. {\"Email\": \"a@b.com\"}"
    )
    fields: dict[str, Any] = Field(
        default_factory=dict,
        description="Column values to set on the matched (or newly created) row",
    )


class UpsertRecordsBody(BaseModel):
    records: list[RecordUpsert]
    add: bool = Field(default=True, description="If false, never create new rows")
    update: bool = Field(default=True, description="If false, never update existing rows")
    on_many: str = Field(
        default="first",
        description='Behavior when multiple rows match "require": "first", "none", or "all".',
    )


class WebhookFields(BaseModel):
    url: str = Field(..., description="URL to notify on matching events")
    event_types: list[str] = Field(
        ..., alias="eventTypes", description='Event types to subscribe to, e.g. ["add", "update"]'
    )
    table_id: str = Field(..., alias="tableId", description="Table to watch")
    enabled: bool = Field(default=True, description="Whether the webhook is active")
    name: str | None = Field(default=None, description="Optional display name")

    model_config = {"populate_by_name": True}


class CreateWebhookBody(BaseModel):
    fields: WebhookFields


class UpdateWebhookBody(BaseModel):
    fields: dict[str, Any] = Field(..., description="Webhook fields to update, e.g. {\"enabled\": false}")


class RunSqlBody(BaseModel):
    sql: str = Field(..., description="SQL SELECT statement (read-only)")
    args: list[Any] | None = Field(
        default=None, description="Parameter values for '?' placeholders in sql"
    )
