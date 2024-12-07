from typing import *

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
    def from_structure(cls, schema: Schema) -> "SchemaReference":
        return cls(name=schema.name, oid=schema.oid)


class TableReference(BaseModel):
    name: str
    oid: int
    schema_: SchemaReference

    @classmethod
    def from_structure(cls, schema: Schema, table: Table) -> "TableReference":
        return cls(
            name=table.name,
            oid=table.oid,
            schema_=SchemaReference.from_structure(schema),
        )


class ColumnReference(BaseModel):
    name: str
    attnum: int
    table: TableReference

    @classmethod
    def from_structure(
        cls, schema: Schema, table: Table, column: Column
    ) -> "ColumnReference":
        return cls(
            name=column.name,
            attnum=column.attnum,
            table=TableReference.from_structure(schema, table),
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


type ResultColumn = Union[ConstantColumn, PrimaryKeyColumn, DataColumn, UnknownColumn]


class Analysis(BaseModel):
    result_columns: List[ResultColumn]
