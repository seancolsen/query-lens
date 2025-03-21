from pglast.ast import Node, SelectStmt, JoinExpr, RangeVar
from pglast.enums import JoinType
from pydantic import BaseModel
from typing import *

from analysis import *
from structure import *


# This maps column names to `ResultColumn` values.
type ColumnsMap = Dict[str, ResultColumn]

# This maps relation names to `ColumnsMap` values.
type RelationsMap = Dict[str, ColumnsMap]

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


class ReferencedRelation(BaseModel):
    ref: RelationReference
    columns: ColumnsMap


def _build_flat_columns_map(schemas_map: SchemasMap) -> FlatColumnsMap:
    result: FlatColumnsMap = dict()
    seen_column_names: Set[str] = set()
    for schema_name, relations_map in schemas_map.items():
        for relation_name, columns in relations_map.items():
            for column_name, column in columns.items():
                if column_name in seen_column_names:
                    continue
                else:
                    relation_reference = RelationReference(
                        name=relation_name, schema_name=schema_name
                    )
                    result[column_name] = ColumnResolution(
                        relation=relation_reference, column=column
                    )
                    seen_column_names.add(column_name)
    return result


def _build_ctes_map(
    database_structure: DatabaseStructure, stmt: SelectStmt
) -> RelationsMap:
    # TODO: Implement this function
    return dict()


def _build_result_columns_from_table(schema: Schema, table: Table) -> ColumnsMap:
    def build_result_column(column: Column) -> ResultColumn:
        column_reference = ColumnReference.from_structure(schema, table, column)
        definition = DataReference(
            ultimate_source=column_reference,
            local_source=None,
        )
        return ResultColumn(name=column.name, definition=definition)

    return {c.name: build_result_column(c) for c in table.columns.values()}


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


class Context:
    _database_structure: DatabaseStructure
    _current_schema: Schema
    _stmt: SelectStmt
    _ctes: RelationsMap

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

    def _resolve_relation(
        self, schema_name: Optional[str], relation_name: str
    ) -> Optional[ColumnsMap]:
        if schema_name:
            schema = self._database_structure.schemas.get(schema_name)
            if schema is None:
                return None
            table = schema.tables.get(relation_name)
            if table is None:
                return None
            return _build_result_columns_from_table(schema, table)
        else:
            cte = self._ctes.get(relation_name)
            if cte:
                return cte
            table = self._current_schema.tables.get(relation_name)
            if not table:
                return None
            return _build_result_columns_from_table(self._current_schema, table)

    def _get_referenced_relations(
        self, node: Node
    ) -> Generator[ReferencedRelation, None, None]:
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

        # `RangeVar` represents a table name, possibly qualified with a schema name.
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
            yield ReferencedRelation(
                ref=RelationReference(name=name, schema_name=node.schemaname),
                columns=columns_map,
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

    def _get_referenced_schemas_map(self) -> SchemasMap:
        relations = self._get_referenced_relations(self._stmt)
        schemas_map: SchemasMap = dict()
        for relation in relations:
            relations_map = schemas_map.get(relation.ref.schema_name, dict())
            relations_map[relation.ref.name] = relation.columns
            schemas_map[relation.ref.schema_name] = relations_map
        return schemas_map

    def create_column_resolver(self) -> ColumnResolver:
        current_schema = self._database_structure.current_schema
        schemas_map = self._get_referenced_schemas_map()
        flat_columns = _build_flat_columns_map(schemas_map)

        def resolve_column(
            schema_name: Optional[str],
            relation_name: Optional[str],
            column_name: str,
        ) -> Optional[ColumnResolution]:
            if relation_name is None:
                return flat_columns.get(column_name)

            relations_map = (
                schemas_map.get(schema_name)
                if schema_name
                else schemas_map.get(current_schema, schemas_map.get(None))
            )
            if relations_map is None:
                return None

            columns = relations_map.get(relation_name)
            if columns is None:
                return None
            column = columns.get(column_name)
            if column is None:
                return None
            return ColumnResolution(
                relation=RelationReference(name=relation_name, schema_name=schema_name),
                column=column,
            )

        return resolve_column
