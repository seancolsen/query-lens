from pglast.ast import Node, SelectStmt, JoinExpr, RangeVar
from pglast.enums import JoinType
from pydantic import BaseModel
from typing import *

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
