from pglast.ast import Node, SelectStmt, JoinExpr, RangeVar
from pydantic import BaseModel
from typing import *

from analysis import *
from structure import *


type ColumnsMap = Dict[str, ResultColumn]
type RelationsMap = Dict[str, ColumnsMap]
type SchemasMap = Dict[Optional[str], RelationsMap]

# schema_name, relation_name, column_name
type ColumnResolver = Callable[
    [Optional[str], Optional[str], str], Optional[ResultColumn]
]


class ReferencedRelation(BaseModel):
    """
    Represents a relation referenced in the FROM clause of a SELECT statement.

    When the relation is aliased:

    - `name` will represent the alias used.
    - `schema_name` will be None.

    When the relation is _not_ aliased:

    - `name` will represent the actual relation name
    - For CTEs, `schema_name` will be None.
    - For tables and views, `schema_name` will be the actual schema name, even if it is
      not explicitly specified when the relation is referenced in the query.
    """

    schema_name: Optional[str] = None
    name: str
    columns: ColumnsMap


def _build_flat_columns_map(schemas: SchemasMap) -> ColumnsMap:
    result: ColumnsMap = dict()
    seen_column_names: Set[str] = set()
    for relation in schemas.values():
        for columns in relation.values():
            for column_name, column in columns.items():
                if column_name in seen_column_names:
                    continue
                else:
                    result[column_name] = column
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
        definition = DataColumnDefinition(
            column_reference=column_reference,
            lookup_column_sets=table.lookup_column_sets,
        )
        return ResultColumn(name=column.name, definition=definition)

    return {c.name: build_result_column(c) for c in table.columns.values()}


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
        if isinstance(node, SelectStmt):
            if not node.fromClause:
                return
            yield from self._get_referenced_relations(node.fromClause)
        elif isinstance(node, RangeVar):
            columns_map = self._resolve_relation(node.schemaname, node.relname)
            if not columns_map:
                raise ValueError(f"Unable to resolve relation: {node}")
            yield ReferencedRelation(
                schema_name=node.schemaname,
                name=node.relname,
                columns=columns_map,
            )
        elif isinstance(node, JoinExpr):
            raise NotImplementedError()
        elif isinstance(node, list) or isinstance(node, tuple):
            for item in node:
                yield from self._get_referenced_relations(item)
        else:
            raise NotImplementedError()

    def _get_referenced_schemas_map(self) -> SchemasMap:
        relations = self._get_referenced_relations(self._stmt)
        schemas_map: SchemasMap = dict()
        for relation in relations:
            relations_map = schemas_map.get(relation.schema_name, dict())
            relations_map[relation.name] = relation.columns
            schemas_map[relation.schema_name] = relations_map
        return schemas_map

    def create_column_resolver(self) -> ColumnResolver:
        current_schema = self._database_structure.current_schema
        schemas_map = self._get_referenced_schemas_map()
        flat_columns = _build_flat_columns_map(schemas_map)

        def resolve_column(
            schema_name: Optional[str],
            relation_name: Optional[str],
            column_name: str,
        ) -> Optional[ResultColumn]:
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
            return columns.get(column_name)

        return resolve_column
