from pydantic import BaseModel


class Column(BaseModel):
    name: str
    attnum: int
    type: str


class Table(BaseModel):
    name: str
    oid: int
    columns: dict[str, Column]
    primary_key: list[str]


class Schema(BaseModel):
    name: str
    oid: int
    tables: dict[str, Table]


class DatabaseStructure(BaseModel):
    schemas: dict[str, Schema]
    current_schema: str
