# Test cases

## Basic constant

```sql
SELECT 1;
```

```json
{
  "result_columns": [
    {
      "classification": "constant",
      "type": "integer"
    }
  ]
}
```

## Basic columns

```sql
SELECT
  id,
  title AS issue_title
FROM issues;
```

```json
{
  "result_columns": [
    {
      "classification": "pk_cell",
      "type": "integer",
      "alias": "id"
    },
    {
      "classification": "data_cell",
      "type": "text",
      "alias": "issue_title",
      "table": "issues",
      "column": "title",
      "pk_lookup_alias": [ "id" ]
    }
  ]
}
```
