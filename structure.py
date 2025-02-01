from pydantic import BaseModel


class Column(BaseModel):
    name: str
    attnum: int
    type: str
    mutable: bool


class LookupColumnSet(BaseModel):
    """
    Represents a set of columns that can be used together to uniquely identify a row in
    a table. Usually this will be only one column, but in the case of multi-column
    primary keys or multi-column unique constraints, there may be more than one column
    in the set.
    """

    column_names: list[str]


class Table(BaseModel):
    name: str
    oid: int
    columns: dict[str, Column]
    lookup_column_sets: list[LookupColumnSet]


class Schema(BaseModel):
    name: str
    oid: int
    tables: dict[str, Table]


class DatabaseStructure(BaseModel):
    schemas: dict[str, Schema]
    current_schema: str
