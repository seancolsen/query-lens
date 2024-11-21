from typing import *

from pydantic import BaseModel


class ConstantColumn(BaseModel):
    classification: str = "constant"
    type: str
    name: Optional[str] = None


class TableReference(BaseModel):
    name: str
    oid: int


class ColumnReference(BaseModel):
    name: str
    attnum: int


class DataColumn(BaseModel):
    classification: str = "data"
    type: str
    table: TableReference
    column: ColumnReference
    name: Optional[str] = None
    primary_key_lookup_names: Optional[List[str]] = None


type ResultColumn = Union[ConstantColumn, DataColumn]


class Analysis(BaseModel):
    result_columns: List[ResultColumn]
