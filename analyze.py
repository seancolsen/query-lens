from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt
from pydantic import BaseModel

from schema import Schema


class ConstantColumn(BaseModel):
    classification: str = "constant"
    type: str
    name: Optional[str] = None


class TableReference(BaseModel):
    name: str
    oid: int


class ColumnReference(BaseModel):
    name: str
    attnum: int


class DataColumn(BaseModel):
    classification: str = "data"
    type: str
    table: TableReference
    column: ColumnReference
    name: Optional[str] = None
    primary_key_lookup_names: Optional[List[str]] = None


type ResultColumn = Union[ConstantColumn, DataColumn]


def analyze_select_stmt(schema: Schema, stmt: SelectStmt) -> List[ResultColumn]:
    pass


def analyze_sql(schema: Schema, query: str):
    try:
        ast = parse_sql(query)
    except Exception as e:
        # TODO decide what return value should be for invalid input
        raise NotImplementedError()

    if len(ast) != 1:
        # TODO decide what return value should be for zero or multi-statement input
        raise NotImplementedError()

    first_statement = ast[0].stmt
    if isinstance(first_statement, SelectStmt):
        return analyze_select_stmt(schema, first_statement)
    else:
        # TODO decide what return value should be for non-SELECT input
        raise NotImplementedError()
