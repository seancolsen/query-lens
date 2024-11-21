# Test cases

All test cases use this sample [issue tracker schema](./test_data/issue_tracker_schema.json).

## Basic constant

```sql
SELECT 1;
```

```json
{
  "result_columns": [
    {
      "classification": "constant",
      "type": "unknown"
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
      "classification": "primary_key",
      "type": "integer",
      "name": "id"
    },
    {
      "classification": "data",
      "type": "text",
      "name": "issue_title",
      "table": {
        "name": "issues",
        "oid": 1
      },
      "column": {
        "name": "title",
        "attnum": 2
      },
      "primary_key_lookup_names": [ "id" ]
    }
  ]
}
```
