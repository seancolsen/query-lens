from typing import *

from pglast import parse_sql
from pglast.ast import (
    SelectStmt,
    Node,
    A_Const,
    ColumnRef,
    String,
    ResTarget,
    JoinExpr,
    RangeVar,
)
from pglast.enums import JoinType
from pydantic import BaseModel

from analysis import *
from structure import *


# This maps relation names to `RelationStructure` values.
type RelationsMap = Dict[str, RelationStructure]

# This maps schema names to `RelationsMap` values. CTEs within the current query are
# stored within an entry with a schema name of `None`.
type SchemasMap = Dict[Optional[str], RelationsMap]


class ColumnResolution(BaseModel):
    relation: RelationReference
    column: ResultColumn


# This maps column names to a (`RelationReference`, `ResultColumn`) tuple. It is
# used to lookup columns by name when a column is referenced without a qualifying
# relation name. The returned `ResultColumn` will be
type FlatColumnsMap = Dict[str, ColumnResolution]

# (schema_name, relation_name, column_name) -> Optional[ColumnResolution]
type ColumnResolver = Callable[
    [Optional[str], Optional[str], str], Optional[ColumnResolution]
]


def _build_flat_columns_map(schemas_map: SchemasMap) -> FlatColumnsMap:
    result: FlatColumnsMap = dict()
    seen_column_names: Set[str] = set()
    for schema_name, relations_map in schemas_map.items():
        for relation_name, relation_structure in relations_map.items():
            for column in relation_structure.result_columns:
                if column.name is None or column.name in seen_column_names:
                    continue
                else:
                    relation_reference = RelationReference(
                        name=relation_name, schema_name=schema_name
                    )
                    result[column.name] = ColumnResolution(
                        relation=relation_reference, column=column
                    )
                    seen_column_names.add(column.name)
    return result


def _build_ctes_map(
    database_structure: DatabaseStructure, stmt: SelectStmt
) -> RelationsMap:
    # TODO: Implement this function
    return dict()


def _assert_node_is_range_var_or_join_expr(node: Node) -> None:
    """
    This checks to make sure a node is either a `RangeVar` (a table reference) or a
    `JoinExpr` (a join) -- or a list/tuple of those. We use this to make sure we're only
    handling AST nodes with simple structures that we already know.
    """
    if isinstance(node, RangeVar) or isinstance(node, JoinExpr):
        return
    elif isinstance(node, list) or isinstance(node, tuple):
        for item in node:
            _assert_node_is_range_var_or_join_expr(item)
    else:
        raise NotImplementedError()


def _build_schemas_map(relations: Iterable[NamedRelation]) -> SchemasMap:
    schemas_map: SchemasMap = dict()
    for relation in relations:
        relations_map = schemas_map.get(relation.reference.schema_name, dict())
        relations_map[relation.reference.name] = relation.structure
        schemas_map[relation.reference.schema_name] = relations_map
    return schemas_map


class Context:
    """
    This stores information about the context of a single SELECT query. It is also used
    recursively within CTEs.
    """

    # ⚠️ It would be nice to consolidate and clean up some of this state (e.g. _ctes vs
    # _relations)

    _database_structure: DatabaseStructure
    _current_schema: Schema
    _stmt: SelectStmt
    _ctes: RelationsMap
    _flat_columns: FlatColumnsMap
    _relations: List[NamedRelation]

    def __init__(self, database_structure: DatabaseStructure, stmt: SelectStmt):
        self._database_structure = database_structure
        current_schema = database_structure.schemas.get(
            database_structure.current_schema
        )
        if not current_schema:
            raise ValueError("Current schema not found in database structure.")
        self._current_schema = current_schema
        self._stmt = stmt

        self._ctes = _build_ctes_map(database_structure, stmt)

        # ⚠️ I don't like how we're calling this instance method within the constructor.
        # It would be nice to refactor this out to avoid uninitialized class properties
        # as the code grows.
        self._relations = list(self._get_referenced_relations(self._stmt))

        self._schemas_map = _build_schemas_map(self._relations)
        self._flat_columns = _build_flat_columns_map(self._schemas_map)

    def _resolve_relation(
        self, schema_name: Optional[str], relation_name: str
    ) -> Optional[RelationStructure]:
        """
        Searches the current scope to find a relation (table/view/CTE) by name
        """
        if schema_name:
            schema = self._database_structure.schemas.get(schema_name)
            if schema is None:
                return None
            table = schema.tables.get(relation_name)
            if table is None:
                return None
            return RelationStructure.from_table(schema, table)
        else:
            cte = self._ctes.get(relation_name)
            if cte:
                return cte
            table = self._current_schema.tables.get(relation_name)
            if not table:
                return None
            return RelationStructure.from_table(self._current_schema, table)

    def _get_referenced_relations(
        self, node: Node
    ) -> Generator[NamedRelation, None, None]:
        """
        Recursively descends the AST of a SELECT statement, yielding ReferencedRelation
        instances to represent all the relations that are referenced within the FROM
        clause.
        """
        # `SelectStmt` represents an entire SELECT statement. Here we recurse into its
        # FROM clause, which should be a table reference or a join expression.
        if isinstance(node, SelectStmt):
            from_clause = node.fromClause
            if not from_clause:
                # This is the case where we're only selecting constant expressions, thus
                # there are no referenced relations.
                return
            _assert_node_is_range_var_or_join_expr(from_clause)
            yield from self._get_referenced_relations(node.fromClause)

        # If we have multiple nodes, we yield from each of them.
        elif isinstance(node, list) or isinstance(node, tuple):
            for item in node:
                yield from self._get_referenced_relations(item)

        # `RangeVar` represents a table/view/CTE name, possibly qualified with a schema
        # name.
        elif isinstance(node, RangeVar):
            columns_map = self._resolve_relation(node.schemaname, node.relname)
            if not columns_map:
                raise ValueError(f"Unable to resolve relation: {node}")
            name = node.relname
            if node.alias:
                if node.alias.colnames:
                    # We have not yet handled column aliases defined in the FROM clause.
                    raise NotImplementedError()
                name = node.alias.aliasname
            yield NamedRelation(
                reference=RelationReference(name=name, schema_name=node.schemaname),
                structure=columns_map,
            )

        # `JoinExpr` represents a JOIN clause. We need to recurse into the left and
        # right.
        elif isinstance(node, JoinExpr):
            if node.alias or node.join_using_alias:
                # `alias` and `join_using_alias` are more esoteric features that we
                # don't need to handle for now. They do NOT represent a table alias.
                raise NotImplementedError()
            if node.jointype not in [JoinType.JOIN_INNER, JoinType.JOIN_LEFT]:
                # We only attempt to handle INNER and LEFT joins for now.
                raise NotImplementedError()
            if node.isNatural:
                # We don't try to handle natural joins for now.
                raise NotImplementedError()
            if node.usingClause:
                # We don't try to handle USING clauses for now.
                raise NotImplementedError()
            _assert_node_is_range_var_or_join_expr(node.larg)
            _assert_node_is_range_var_or_join_expr(node.rarg)
            yield from self._get_referenced_relations(node.larg)
            yield from self._get_referenced_relations(node.rarg)

        else:
            raise NotImplementedError()

    def resolve_column(
        self,
        schema_name: Optional[str],
        relation_name: Optional[str],
        column_name: str,
    ) -> Optional[ColumnResolution]:
        current_schema = self._database_structure.current_schema

        if relation_name is None:
            return self._flat_columns.get(column_name)

        relations_map = (
            self._schemas_map.get(schema_name)
            if schema_name
            else self._schemas_map.get(current_schema, self._schemas_map.get(None))
        )
        if relations_map is None:
            return None

        relation_structure = relations_map.get(relation_name)
        if relation_structure is None:
            return None
        column = relation_structure.get_column(column_name)
        if column is None:
            return None
        return ColumnResolution(
            relation=RelationReference(name=relation_name, schema_name=schema_name),
            column=column,
        )

    def get_relations(self) -> List[NamedRelation]:
        return self._relations


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
