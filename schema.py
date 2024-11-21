from dataclasses import dataclass


@dataclass
class Column:
    name: str
    attnum: int
    type: str


@dataclass
class Table:
    name: str
    oid: int
    columns: dict[str, Column]
    primary_key: list[str]


@dataclass
class Schema:
    name: str
    oid: int
    tables: dict[str, Table]
