from typing import *

from pydantic import BaseModel, Field

from structure import Column, Table, Schema, LookupColumnSet, RelationReference


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


class Analysis(BaseModel):
    result_columns: List[ResultColumn]
