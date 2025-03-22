from pydantic import BaseModel
from typing import *


class RelationReference(BaseModel):
    """
    Represents a relation referenced locally in a query. It could be a table, a view, or
    a CTE.

    When the relation is aliased:

    - `name` will represent the alias used.
    - `schema_name` will be None.

    When the relation is _not_ aliased:

    - `name` will represent the actual relation name
    - For CTEs, `schema_name` will be None.
    - For tables and views, `schema_name` will be the actual schema name, even if it is
      not explicitly specified when the relation is referenced in the query.
    """

    name: str
    schema_name: Optional[str] = None


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
