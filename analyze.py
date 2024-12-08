from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef, String, ResTarget

from analysis import *
from context import Context, ColumnResolver
from structure import DatabaseStructure


def _deduce_result_column_definition(
    resolve_column: ColumnResolver, expr: Node
) -> ColumnDefinition:
    if isinstance(expr, A_Const):
        return ConstantColumnDefinition(type="unknown")

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
            return UnknownColumnDefinition(reason=reason)
        column = resolve_column(schema_name, table_name, column_name)
        return (
            column.definition
            if column
            else UnknownColumnDefinition(reason="Unable to resolve column.")
        )

    else:
        raise NotImplementedError()


def _deduce_result_column_name(expr: Node) -> Optional[str]:
    if isinstance(expr, ColumnRef):
        return expr.fields[-1].sval
    else:
        # TODO we could get more clever here to handle additional cases. For example,
        # PostgreSQL will name a `count(*)` column as `count`. We could handle that here
        # and other similar cases.
        return None


def _deduce_result_columns(database_structure: DatabaseStructure, stmt: SelectStmt):
    context = Context(database_structure, stmt)
    column_resolver = context.create_column_resolver()

    for expr in stmt.targetList:
        res_target: ResTarget = expr
        if res_target.indirection is not None:
            # The AST has an 'indirection' field here.
            #
            # https://pglast.readthedocs.io/en/v7/ast.html#pglast.ast.ResTarget
            #
            # I don't understand it well enough so I'm erring on the side of caution by
            # raising an error if encountered.
            raise NotImplementedError()

        definition = _deduce_result_column_definition(column_resolver, res_target.val)
        name = res_target.name or _deduce_result_column_name(res_target.val)
        yield ResultColumn(definition=definition, name=name)


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
