from typing import *

from pydantic import BaseModel, Field

from structure import Column, Table, Schema, LookupColumnSet


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
    table_reference: TableReference
    column: Column

    @classmethod
    def from_structure(cls, schema: Schema, table: Table, column: Column) -> Self:
        return cls(
            table_reference=TableReference.from_structure(schema, table),
            column=column,
        )


class ConstantColumnDefinition(BaseModel):
    classification: Literal["constant"] = "constant"
    type: str


class DataColumnDefinition(BaseModel):
    classification: Literal["data"] = "data"
    column_reference: ColumnReference
    lookup_column_sets: List[LookupColumnSet]


class UnknownColumnDefinition(BaseModel):
    classification: Literal["unknown"] = "unknown"
    reason: Optional[str] = None


type ColumnDefinition = Union[
    ConstantColumnDefinition,
    DataColumnDefinition,
    UnknownColumnDefinition,
]


class ResultColumn(BaseModel):
    definition: ColumnDefinition = Field(discriminator="classification")
    name: Optional[str] = None


class Analysis(BaseModel):
    result_columns: List[ResultColumn]
