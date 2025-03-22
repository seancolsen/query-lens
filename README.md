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

## Development loop

This is the process I've been following during development:

1. Run an interactive debugger against a single test case.

    (Development will likely be _arduous_ without an interactive debugger!)

    For VS Code, this configuration seems to work well in `.vscode/launch.json`:

    ```json
    {
      "version": "0.2.0",
      "configurations": [
        {
          "name": "One case",
          "type": "python",
          "request": "launch",
          "module": "pytest",
          "args": [
            "tests/test_cases.py::test_straightforward_cases[case3]",
            "-s",
            "--capture=no"
          ],
          "console": "integratedTerminal",
          "justMyCode": false
        }
      ]
    }
    ```

    Change the number in `[case3]` to a different index to test a different case.

1. In the test cases markdown file, write the SQL first.

1. For the expected JSON, begin with an empty block of result columns, like this:

    ```json
    {
      "result_columns": [],
      "pk_mappings": []
    }
    ```

    This way the expected result will validate into a `RelationStructure` but will surely fail the test assertion.

1. Run the test. See where it's failing. Set breakpoints to inspect the data structures near the failure, stepping backwards up the call stack as necessary.

1. Refer to the [pglast AST docs](https://pglast.readthedocs.io/en/v7/ast.html) to understand each AST node.
    - For example, if you have a `RangeVar` node, search that docs page for `pglast.ast.RangeVar`.
    - The pglast docs have _some_ info on AST nodes, but the most useful info is directly in the `libpg_query` source code. Look for text like:

        > Wrapper for the [homonymous](https://github.com/pganalyze/libpg_query/blob/27b2af9/src/postgres/include/nodes/primnodes.h#L71) parser node.

        Click on "homonymous" to read the `libpg_query` source code for the node. It usually has a bunch more comments.

1. If the test is producing a valid `RelationStructure` for `actual`, then you can run the following from the debug console:

    ```
    actual.json()
    ```

    This will give you JSON that you can copy and format using your editor. Inspect it to make sure it's correct. Then copy-paste it into the expected result section within the markdown test case.
