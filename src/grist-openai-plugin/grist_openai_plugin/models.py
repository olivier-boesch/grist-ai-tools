"""Pydantic request/response models for the Grist GPT Action."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    error: str
    status_code: int


class NameBody(BaseModel):
    name: str = Field(..., description="Display name")


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


class AddTablesBody(BaseModel):
    tables: list[TableDef]


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


class RunSqlBody(BaseModel):
    sql: str = Field(..., description="SQL SELECT statement (read-only)")
    args: list[Any] | None = Field(
        default=None, description="Parameter values for '?' placeholders in sql"
    )
