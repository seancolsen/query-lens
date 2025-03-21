from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef, String, ResTarget

from analysis import *
from context import Context, ColumnResolver
from structure import DatabaseStructure


def _deduce_result_column_name(expr: Node) -> Optional[str]:
    if isinstance(expr, ColumnRef):
        return expr.fields[-1].sval
    else:
        # We could get more clever here to handle additional cases. For example,
        # PostgreSQL will name a `count(*)` column as `count`. We could handle that here
        # and other similar cases.
        return None


def _analyze_result_column(
    resolve_column: ColumnResolver, expr: Node, alias: Optional[str]
) -> ResultColumn:
    name = alias or _deduce_result_column_name(expr)

    def unknown_column(reason: str) -> ResultColumn:
        return ResultColumn(definition=UnknownExpression(reason=reason), name=name)

    if isinstance(expr, A_Const):
        return ResultColumn(definition=ConstantValue(type="unknown"), name=name)

    if isinstance(expr, ColumnRef):
        fields: List[String] = expr.fields
        schema_name: Optional[str] = None
        relation_name: Optional[str] = None
        if len(fields) == 1:
            column_name = fields[0].sval
        elif len(fields) == 2:
            relation_name = fields[0].sval
            column_name = fields[1].sval
        elif len(fields) == 3:
            schema_name = fields[0].sval
            relation_name = fields[1].sval
            column_name = fields[2].sval
        else:
            reason = f"Unsupported number of ColumnRef fields. Expected 1-3. Got {len(fields)}."
            return unknown_column(reason)

        if not isinstance(column_name, str):
            reason = "Unable to identify string column in within AST."
            return unknown_column(reason)

        column_resolution = resolve_column(schema_name, relation_name, column_name)
        if column_resolution is None:
            return unknown_column("Unable to resolve column.")

        column = column_resolution.column

        local_column_reference = LocalColumnReference(
            relation=column_resolution.relation,
            column_name=column_name,
        )
        return column.recontextualize(local_column_reference, name)

    else:
        raise NotImplementedError()


def _analyze_result_columns(database_structure: DatabaseStructure, stmt: SelectStmt):
    context = Context(database_structure, stmt)
    resolve_column = context.create_column_resolver()

    for res_target in stmt.targetList:
        if not isinstance(res_target, ResTarget):
            raise ValueError(f"Unexpected statement target: {type(res_target)}")
        if res_target.indirection is not None:
            # The AST has an 'indirection' field here.
            #
            # https://pglast.readthedocs.io/en/v7/ast.html#pglast.ast.ResTarget
            #
            # I don't understand it well enough so I'm erring on the side of caution by
            # raising an error if encountered.
            raise NotImplementedError()

        yield _analyze_result_column(resolve_column, res_target.val, res_target.name)


def analyze_sql(database_structure: DatabaseStructure, sql: str):
    try:
        ast = parse_sql(sql)
    except Exception as e:
        # Invalid input
        raise NotImplementedError()

    if len(ast) != 1:
        # Zero or multi-statement input
        raise NotImplementedError()

    first_statement = ast[0].stmt
    if isinstance(first_statement, SelectStmt):
        return Analysis(
            result_columns=list(
                _analyze_result_columns(database_structure, first_statement)
            )
        )
    else:
        # Non-SELECT input
        raise NotImplementedError()
