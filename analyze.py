from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef, String

from analysis import *
from context import Context, ColumnResolver
from structure import DatabaseStructure


def _deduce_result_column(resolve_column: ColumnResolver, expr: Node) -> ResultColumn:
    if isinstance(expr, A_Const):
        return ConstantColumn(type="unknown")

    if isinstance(expr, ColumnRef):
        fields: Tuple[String] = expr.fields
        column = None
        schema_name = None
        table_name = None
        if len(fields) == 1:
            column_name = fields[0].sval
        elif len(fields) == 2:
            table_name = fields[0].sval
            column_name = fields[1].sval
        elif len(fields) == 3:
            schema_name = fields[0].sval
            table_name = fields[1].sval
            column_name = fields[2].sval
        else:
            reason = f"Unsupported number of ColumnRef fields. Expected 1-3. Got {len(fields)}."
            return UnknownColumn(reason=reason)
        column = resolve_column(schema_name, table_name, column_name)
        return column if column else UnknownColumn(reason="Unable to resolve column.")

    else:
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
