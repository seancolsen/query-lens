# Query Lens

Query Lens is a static analysis tool for PostgreSQL queries.

## Setup

```
python3 -m venv venv 
source venv/bin/activate
pip install -r ./requirements.txt 
```

## Run CLI

```
./query-lens.py -s ./tests/test_data/issue_tracker_schema.json -q 'SELECT 1;'
```

## Run tests

```
pytest .
```

## Check types

```
mypy .
```

## Development resources

- [pglast AST docs](https://pglast.readthedocs.io/en/v7/ast.html)
