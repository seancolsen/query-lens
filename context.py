from pglast.ast import SelectStmt

from schema import Schema


class Context:
    schema: Schema
    stmt: SelectStmt

    def __init__(self, schema: Schema, stmt: SelectStmt):
        self.schema = schema
        self.stmt = stmt
