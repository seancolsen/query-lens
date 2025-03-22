from typing import *

from pglast import parse_sql
from pglast.ast import SelectStmt, Node, A_Const, ColumnRef, String, ResTarget

from analysis import *
from context import Context
from structure import DatabaseStructure


def _deduce_result_column_name(expr: Node) -> Optional[str]:
    if isinstance(expr, ColumnRef):
        return expr.fields[-1].sval
    else:
        # We could get more clever here to handle additional cases. For example,
        # PostgreSQL will name a `count(*)` column as `count`. We could handle that here
        # and other similar cases.
        return None


def _build_result_column(cx: Context, expr: Node, alias: Optional[str]) -> ResultColumn:
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

        column_resolution = cx.resolve_column(schema_name, relation_name, column_name)
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


def _build_result_columns(cx: Context, stmt: SelectStmt):
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

        yield _build_result_column(cx, res_target.val, res_target.name)


def _get_column_local_source(column: ResultColumn) -> Optional[LocalColumnReference]:
    if not isinstance(column.definition, DataReference):
        return None
    return column.definition.local_source


def _build_pk_mappings(
    cx: Context, outer_columns: List[ResultColumn]
) -> List[PkMapping]:
    # ⚠️ The nested loops in this function are not great for performance. We're probably
    # not dealing with large lists here. But this is an area of code that is ripe for
    # performance improvement!
    mappings: List[PkMapping] = list()
    for sub_relation in cx.get_relations():
        for sub_mapping in sub_relation.structure.pk_mappings:

            def find_outer_pk_column(inner_pk_column_name: str) -> Optional[str]:
                for outer_column in outer_columns:
                    outer_column_source = _get_column_local_source(outer_column)
                    if outer_column_source is None:
                        return None
                    if (
                        outer_column_source.relation == sub_relation.reference
                        and outer_column_source.column_name == inner_pk_column_name
                    ):
                        return outer_column.name
                return None

            def get_pk_columns() -> Optional[List[str]]:
                result: List[str] = []
                for c in sub_mapping.pk_columns:
                    i = find_outer_pk_column(c)
                    if i is None:
                        return None
                    result.append(i)
                return result

            pk_columns = get_pk_columns()
            if pk_columns is None:
                # If the outer relation doesn't contain all PK columns of the inner
                # PkMapping, then we can't lift the inner PkMapping up to the outer one.
                continue

            data_columns: List[str] = []
            for column in outer_columns:
                if column.name is None:
                    # Skip columns that don't have names
                    continue
                if not isinstance(column.definition, DataReference):
                    # Skip columns that aren't data references
                    continue
                if column.definition.local_source is None:
                    # This should not happen because we're in a query not a table
                    continue
                column_source_relation = column.definition.local_source.relation
                if column_source_relation != sub_relation.reference:
                    # Skip pairings where the inner loop over columns produces a column
                    # that don't fall within the relation produced by the outer loop.
                    continue
                if (
                    column.definition.local_source.column_name
                    not in sub_mapping.data_columns
                ):
                    # Only use the column if it's a data column within the current
                    # sub_mapping
                    continue
                data_columns.append(column.name)

            # If data_columns is empty, we still include the PkMapping. I'm not sure if
            # this is the behavior we'll ultimately want, but for now I figure it's
            # better to include it on the off chance that it's somehow useful later on.

            mappings.append(PkMapping(pk_columns=pk_columns, data_columns=data_columns))

    return mappings


def _analyze_select_statement(
    database_structure: DatabaseStructure, statement: SelectStmt
) -> RelationStructure:
    cx = Context(database_structure, statement)
    result_columns = list(_build_result_columns(cx, statement))
    pk_mappings = _build_pk_mappings(cx, result_columns)
    return RelationStructure(
        result_columns=result_columns,
        pk_mappings=pk_mappings,
    )


def analyze_sql(database_structure: DatabaseStructure, sql: str) -> RelationStructure:
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
        return _analyze_select_statement(database_structure, first_statement)
    else:
        # Non-SELECT input
        raise NotImplementedError()
