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
      "definition": {
        "classification": "constant",
        "type": "unknown"
      },
      "name": null
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
      "definition": {
        "classification": "data",
        "column_reference": {
          "table_reference": {
            "name": "issues",
            "oid": 2,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "id",
            "attnum": 1,
            "type": "integer",
            "mutable": false
          }
        },
        "lookup_column_sets": [
          {
            "column_names": [
              "id"
            ]
          }
        ]
      },
      "name": "id"
    },
    {
      "definition": {
        "classification": "data",
        "column_reference": {
          "table_reference": {
            "name": "issues",
            "oid": 2,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "title",
            "attnum": 2,
            "type": "text",
            "mutable": true
          }
        },
        "lookup_column_sets": [
          {
            "column_names": [
              "id"
            ]
          }
        ]
      },
      "name": "issue_title"
    }
  ]
}
```


## Joins

```sql
SELECT
  issue.id,
  issue.title,
  author.username as author,
  team.name as team
FROM issues as issue
LEFT JOIN users as author ON author.id = issue.author
LEFT JOIN teams as team ON team.id = author.team
```

```json
{
  "result_columns": [
    {
      "name": "id",
      "definition": {
        "classification": "primary_key",
        "type": "integer",
        "column_reference": {
          "name": "id",
          "attnum": 1,
          "table_reference": {
            "name": "issues",
            "oid": 2,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          }
        }
      }
    },
    {
      "name": "title",
      "definition": {
        "classification": "data",
        "type": "text",
        "column_reference": {
          "name": "title",
          "attnum": 2,
          "table_reference": {
            "name": "issues",
            "oid": 2,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          }
        }
      }
    },
    {
      "name": "author",
      "definition": {
        "classification": "data",
        "type": "text",
        "column_reference": {
          "name": "username",
          "attnum": 2,
          "table_reference": {
            "name": "users",
            "oid": 3,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          }
        }
      }
    },
    {
      "name": "team",
      "definition": {
        "classification": "data",
        "type": "text",
        "column_reference": {
          "name": "name",
          "attnum": 2,
          "table_reference": {
            "name": "teams",
            "oid": 4,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          }
        }
      }
    }
  ]
}
```


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
