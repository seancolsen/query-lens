from typing import *

from pydantic import BaseModel, Field

from structure import Column, Table, Schema


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


class ConstantColumnDefinition(BaseModel):
    classification: Literal["constant"] = "constant"
    type: str


class PrimaryKeyColumnDefinition(BaseModel):
    classification: Literal["primary_key"] = "primary_key"
    type: str
    column_reference: ColumnReference


class DataColumnDefinition(BaseModel):
    classification: Literal["data"] = "data"
    type: str
    column_reference: ColumnReference
    primary_key_lookup_names: Optional[List[str]] = None


class UnknownColumnDefinition(BaseModel):
    classification: Literal["unknown"] = "unknown"
    reason: Optional[str] = None


type ColumnDefinition = Union[
    ConstantColumnDefinition,
    PrimaryKeyColumnDefinition,
    DataColumnDefinition,
    UnknownColumnDefinition,
]


class ResultColumn(BaseModel):
    definition: ColumnDefinition = Field(discriminator="classification")
    name: Optional[str] = None


class Analysis(BaseModel):
    result_columns: List[ResultColumn]
