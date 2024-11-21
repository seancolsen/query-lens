from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef

from analysis import *
from context import Context
from schema import Schema


def analyze_result_column_expr(cx: Context, expr: Node) -> ResultColumn:
    if isinstance(expr, A_Const):
        return ConstantColumn(type="unknown")
    if isinstance(expr, ColumnRef):
        return ConstantColumn(type="unknown")
    raise NotImplementedError()


def analyze_select_stmt(schema: Schema, stmt: SelectStmt):
    cx = Context(schema, stmt)
    for expr in stmt.targetList:
        if expr.indirection is not None:
            # The AST has an 'indirection' field here. I'm not sure what it
            # might be for, so I'm erring on the side of caution by raising an
            # error if I encounter it.
            raise NotImplementedError()
        yield analyze_result_column_expr(cx, expr.val)


def analyze_sql(schema: Schema, sql: str):
    try:
        ast = parse_sql(sql)
    except Exception as e:
        # TODO decide what return value should be for invalid input
        raise NotImplementedError()

    if len(ast) != 1:
        # TODO decide what return value should be for zero or multi-statement input
        raise NotImplementedError()

    first_statement = ast[0].stmt
    if isinstance(first_statement, SelectStmt):
        return Analysis(
            result_columns=list(analyze_select_stmt(schema, first_statement))
        )
    else:
        # TODO decide what return value should be for non-SELECT input
        raise NotImplementedError()
