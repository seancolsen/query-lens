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
        "ultimate_source": {
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
        "local_source": {
          "relation": {
            "name": "issues",
            "schema_name": null
          },
          "column_name": "id"
        }
      },
      "name": "id"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
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
        "local_source": {
          "relation": {
            "name": "issues",
            "schema_name": null
          },
          "column_name": "title"
        }
      },
      "name": "issue_title"
    }
  ]
}
```

## Simple join 

```sql
SELECT
  u.id as user_id,
  u.username as username,
  t.id as team_id,
  t.name as team_name
FROM users u
JOIN teams AS t on t.id = u.team
```

```json
{
  "result_columns": [
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "users",
            "oid": 1,
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
        "local_source": {
          "relation": {
            "name": "u",
            "schema_name": null
          },
          "column_name": "id"
        }
      },
      "name": "user_id"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "users",
            "oid": 1,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "username",
            "attnum": 2,
            "type": "text",
            "mutable": true
          }
        },
        "local_source": {
          "relation": {
            "name": "u",
            "schema_name": null
          },
          "column_name": "username"
        }
      },
      "name": "username"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "teams",
            "oid": 9,
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
        "local_source": {
          "relation": {
            "name": "t",
            "schema_name": null
          },
          "column_name": "id"
        }
      },
      "name": "team_id"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "teams",
            "oid": 9,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "name",
            "attnum": 2,
            "type": "text",
            "mutable": true
          }
        },
        "local_source": {
          "relation": {
            "name": "t",
            "schema_name": null
          },
          "column_name": "name"
        }
      },
      "name": "team_name"
    }
  ]
}
```

## Multiple joins

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
      "definition": {
        "classification": "data",
        "ultimate_source": {
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
        "local_source": {
          "relation": {
            "name": "issue",
            "schema_name": null
          },
          "column_name": "id"
        }
      },
      "name": "id"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
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
        "local_source": {
          "relation": {
            "name": "issue",
            "schema_name": null
          },
          "column_name": "title"
        }
      },
      "name": "title"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "users",
            "oid": 1,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "username",
            "attnum": 2,
            "type": "text",
            "mutable": true
          }
        },
        "local_source": {
          "relation": {
            "name": "author",
            "schema_name": null
          },
          "column_name": "username"
        }
      },
      "name": "author"
    },
    {
      "definition": {
        "classification": "data",
        "ultimate_source": {
          "table_reference": {
            "name": "teams",
            "oid": 9,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "name",
            "attnum": 2,
            "type": "text",
            "mutable": true
          }
        },
        "local_source": {
          "relation": {
            "name": "team",
            "schema_name": null
          },
          "column_name": "name"
        }
      },
      "name": "team"
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
