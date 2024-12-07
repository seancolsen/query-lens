from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef

from analysis import *
from context import Context, ColumnResolver
from structure import DatabaseStructure


def _deduce_result_column(resolve_column: ColumnResolver, expr: Node) -> ResultColumn:
    if isinstance(expr, A_Const):
        return ConstantColumn(type="unknown")
    if isinstance(expr, ColumnRef):
        # TODO: continue building this out by picking apart the ColumnRef fields
        # column = cx.resolve_column()
        return UnknownColumn()
    raise NotImplementedError()


def _deduce_result_columns(database_structure: DatabaseStructure, stmt: SelectStmt):
    context = Context(database_structure, stmt)
    column_resolver = context.create_column_resolver()

    for expr in stmt.targetList:
        if expr.indirection is not None:
            # The AST has an 'indirection' field here. I'm not sure what it
            # might be for, so I'm erring on the side of caution by raising an
            # error if I encounter it.
            raise NotImplementedError()
        yield _deduce_result_column(column_resolver, expr.val)


def analyze_sql(database_structure: DatabaseStructure, sql: str):
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
            result_columns=list(
                _deduce_result_columns(database_structure, first_statement)
            )
        )
    else:
        # TODO decide what return value should be for non-SELECT input
        raise NotImplementedError()
