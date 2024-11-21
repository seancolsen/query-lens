from pglast import parse_sql
from pglast.ast import SelectStmt

from schema import Schema


def analyze_select_stmt(schema: Schema, stmt: SelectStmt):
    pass


def analyze_sql(schema, query: str):
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
