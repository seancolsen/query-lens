from typing import *

from pydantic import BaseModel, Field

from structure import Column, Table, Schema, RelationReference


class SchemaReference(BaseModel):
    name: str
    oid: int

    @classmethod
    def from_structure(cls, schema: Schema) -> Self:
        return cls(name=schema.name, oid=schema.oid)


class TableReference(BaseModel):
    name: str
    oid: int
    schema_reference: SchemaReference

    @classmethod
    def from_structure(cls, schema: Schema, table: Table) -> Self:
        return cls(
            name=table.name,
            oid=table.oid,
            schema_reference=SchemaReference.from_structure(schema),
        )


class ColumnReference(BaseModel):
    table_reference: TableReference
    column: Column

    @classmethod
    def from_structure(cls, schema: Schema, table: Table, column: Column) -> Self:
        return cls(
            table_reference=TableReference.from_structure(schema, table),
            column=column,
        )


class LocalColumnReference(BaseModel):
    relation: RelationReference
    column_name: str


class ConstantValue(BaseModel):
    classification: Literal["constant"] = "constant"
    type: str


class DataReference(BaseModel):
    """
    Represents a reference to data within the context of a relation (table or query).

    - `ultimate_source` — This property tracks the original source of the data, i.e. an
      actual Postgres schema, table, and column. It is contextually INDEPENDENT, so it
      can be passed up through CTEs without modification

    - `local_source` — This property tracks where this data came from within the context
      of the current relation. If the contextual relation is an actual table, then this
      property will be None. If the contextual relation is a query, then this property
      will point to the a relation referenced from the query (and to a specific column
      within that relation). This property is CONTEXTUALLY DEPENDENT, so it will need to
      be recontextualized if passed up through CTEs.
    """

    classification: Literal["data"] = "data"
    ultimate_source: ColumnReference
    local_source: Optional[LocalColumnReference]


class UnknownExpression(BaseModel):
    classification: Literal["unknown"] = "unknown"
    reason: Optional[str] = None


type ColumnDefinition = Union[
    ConstantValue,
    DataReference,
    UnknownExpression,
]


def _recontextualize_column_definition(
    definition: ColumnDefinition, local_source: LocalColumnReference
) -> ColumnDefinition:
    if isinstance(definition, DataReference):
        return DataReference(
            ultimate_source=definition.ultimate_source,
            local_source=local_source,
        )
    return definition


class ResultColumn(BaseModel):
    """
    Represents one column within the context of a relation (table or query).

    - `definition` — This property describes the data in the column. This property is
      CONTEXTUALLY DEPENDENT, so it will need to be recontextualized if passed up
      through CTEs.

    - `name` — This property is the name of the column within the context of the
      relation. If the column is aliased in the query, this will be the alias. It will
      be None in cases where we're not easily able to determine the name that Postgres
      auto-assigns to expressions.
    """

    definition: ColumnDefinition = Field(discriminator="classification")
    name: Optional[str] = None

    def recontextualize(
        self, local_column_reference: LocalColumnReference, alias: Optional[str] = None
    ) -> "ResultColumn":
        return ResultColumn(
            definition=_recontextualize_column_definition(
                self.definition, local_column_reference
            ),
            name=alias or self.name,
        )

    @classmethod
    def from_table_column(cls, schema: Schema, table: Table, column: Column) -> Self:
        column_reference = ColumnReference.from_structure(schema, table, column)
        definition = DataReference(
            ultimate_source=column_reference,
            local_source=None,
        )
        return cls(name=column.name, definition=definition)


class PkMapping(BaseModel):
    """
    This represents a mapping between some columns in a relation that can be used as a
    basis for updating cells of other columns in the relation.

    Actual tables will usually have one PkMapping. There can be multiple if there are
    multiple UNIQUE NOT NULL keys present (e.g. an identity `id` column plus a `uuid`
    column). And if there are no unique kys, then there will be not PkMappings.

    A relation originating from a query might have multiple PkMappings if the query
    joins multiple tables together.

    - `pk_columns` — This property is a list of column names that, together, uniquely
      identify a _portion_ of a row in the relation. Commonly, it will only contain one
      column name, but it could contain more than one in the case of a composite key.
    - `data_columns` — This property is a list of column names that can be updated when
      the `pk_columns` are known.
    """

    pk_columns: List[str]
    data_columns: List[str]


def _build_pk_mappings_from_table(table: Table) -> Generator[PkMapping, None, None]:
    for lookup_column_set in table.lookup_column_sets:
        column_names = lookup_column_set.column_names
        data_columns = [c for c in table.columns if c not in column_names]
        yield PkMapping(pk_columns=column_names, data_columns=data_columns)


class RelationStructure(BaseModel):
    result_columns: List[ResultColumn]
    pk_mappings: List[PkMapping]

    def get_column(self, name: str) -> Optional[ResultColumn]:
        # Perf could be improved here by building, caching, and using a dict
        return next((c for c in self.result_columns if c.name == name), None)

    @classmethod
    def from_table(cls, schema: Schema, table: Table) -> Self:
        def build_result_column(column: Column) -> ResultColumn:
            return ResultColumn.from_table_column(schema, table, column)

        result_columns = [build_result_column(c) for c in table.columns.values()]
        pk_mappings = list(_build_pk_mappings_from_table(table))

        return cls(result_columns=result_columns, pk_mappings=pk_mappings)


class NamedRelation(BaseModel):
    reference: RelationReference
    structure: RelationStructure
