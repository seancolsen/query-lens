# Test cases

All test cases use this sample [issue tracker schema](./test_data/issue_tracker_schema.json).

## Playground

```sql
WITH
foo(v) AS (
  SELECT 'bar'
),
labels AS (
  SELECT
    il.issue,
    array_agg(label) AS labels
  FROM labels
  JOIN issue_labels il ON il.label = labels.id
  GROUP BY il.issue
)
SELECT
  public.issues.id,
  issues.title,
  issues.status AS stat,
  due_date,
  author.username,
  email,
  labels.labels,
  foo.v
FROM issues
LEFT JOIN public.users author ON users.id = issues.author
LEFT JOIN labels ON labels.issue = issues.id
CROSS JOIN foo;
```

```json
"TODO"
```

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
      "name": "id",
      "column_reference": {
        "name": "id",
        "attnum": 1,
        "table_reference": {
          "name": "issues",
          "oid": 1,
          "schema_reference": {
            "name": "public",
            "oid": 2200
          }
        }
      }
    },
    {
      "classification": "data",
      "type": "text",
      "name": "issue_title",
      "column_reference": {
        "name": "title",
        "attnum": 2,
        "table_reference": {
          "name": "issues",
          "oid": 1,
          "schema_reference": {
            "name": "public",
            "oid": 2200
          }
        }
      },
      "primary_key_lookup_names": [ "id" ]
    }
  ]
}
```
