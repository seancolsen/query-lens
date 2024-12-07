from typing import *
import json

from pydantic import BaseModel

from structure import Column, Table, Schema


class ConstantColumn(BaseModel):
    classification: str = "constant"
    type: str
    name: Optional[str] = None


class SchemaReference(BaseModel):
    name: str
    oid: int

    @classmethod
    def from_structure(cls, schema: Schema) -> Self:
        return cls(name=schema.name, oid=schema.oid)


class TableReference(BaseModel):
    name: str
    oid: int
    schema_reference: SchemaReference

    @classmethod
    def from_structure(cls, schema: Schema, table: Table) -> Self:
        return cls(
            name=table.name,
            oid=table.oid,
            schema_reference=SchemaReference.from_structure(schema),
        )


class ColumnReference(BaseModel):
    name: str
    attnum: int
    table_reference: TableReference

    @classmethod
    def from_structure(cls, schema: Schema, table: Table, column: Column) -> Self:
        return cls(
            name=column.name,
            attnum=column.attnum,
            table_reference=TableReference.from_structure(schema, table),
        )


class PrimaryKeyColumn(BaseModel):
    classification: str = "primary_key"
    type: str
    column_reference: ColumnReference
    name: Optional[str] = None


class DataColumn(BaseModel):
    classification: str = "data"
    type: str
    column_reference: ColumnReference
    name: Optional[str] = None
    primary_key_lookup_names: Optional[List[str]] = None


class UnknownColumn(BaseModel):
    classification: str = "unknown"
    reason: Optional[str] = None


type ResultColumn = Union[ConstantColumn, PrimaryKeyColumn, DataColumn, UnknownColumn]


class Analysis(BaseModel):
    result_columns: List[ResultColumn]

    @classmethod
    def model_validate_json(
        cls,
        json_data: str | bytes | bytearray,
        *,
        strict: bool | None = None,
        context: Any | None = None,
    ) -> Self:
        data = json.loads(json_data)
        result_columns: List[ResultColumn] = []
        for column_data in data.get("result_columns", []):
            classification = column_data.get("classification")
            if classification == "constant":
                result_columns.append(ConstantColumn.model_validate(column_data))
            elif classification == "primary_key":
                result_columns.append(PrimaryKeyColumn.model_validate(column_data))
            elif classification == "data":
                result_columns.append(DataColumn.model_validate(column_data))
            elif classification == "unknown":
                result_columns.append(UnknownColumn.model_validate(column_data))
            else:
                raise ValueError(f"Unknown classification: {classification}")
        return cls(result_columns=result_columns)
