#!/usr/bin/env python

import argparse
import sys

from structure import DatabaseStructure
from analyze import analyze_sql

parser = argparse.ArgumentParser(description="SQL static analysis tool.")
query_help = "The SQL query to analyze. Will be read from STDIN if not provided."
parser.add_argument("-q", required=False, help=query_help)
structure_help = "Path to the database structure JSON file"
parser.add_argument("-s", required=True, help=structure_help)
args = parser.parse_args()


def get_structure() -> DatabaseStructure:
    with open(args.s) as f:
        return DatabaseStructure.model_validate_json(f.read())


def get_query() -> str:
    param = args.q
    if param:
        return param
    return sys.stdin.read()


analysis = analyze_sql(get_structure(), get_query())

print(analysis.model_dump_json(indent=2))
