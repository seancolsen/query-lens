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
  ],
  "pk_mappings": []
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
  ],
  "pk_mappings": [
    {
      "pk_columns": [
        "id"
      ],
      "data_columns": [
        "issue_title"
      ]
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
  ],
  "pk_mappings": [
    {
      "pk_columns": [
        "user_id"
      ],
      "data_columns": [
        "username"
      ]
    },
    {
      "pk_columns": [
        "team_id"
      ],
      "data_columns": [
        "team_name"
      ]
    }
  ]
}
```

## Multiple joins

```sql
SELECT
  issue.id          as issue_id,
  issue.title       as title,
  issue.description as description,
  author.id         as author_id,
  author.username   as author,
  team.name         as team
FROM issues     as issue
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
      "name": "issue_id"
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
            "name": "issues",
            "oid": 2,
            "schema_reference": {
              "name": "public",
              "oid": 2200
            }
          },
          "column": {
            "name": "description",
            "attnum": 3,
            "type": "text",
            "mutable": true
          }
        },
        "local_source": {
          "relation": {
            "name": "issue",
            "schema_name": null
          },
          "column_name": "description"
        }
      },
      "name": "description"
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
            "name": "id",
            "attnum": 1,
            "type": "integer",
            "mutable": false
          }
        },
        "local_source": {
          "relation": {
            "name": "author",
            "schema_name": null
          },
          "column_name": "id"
        }
      },
      "name": "author_id"
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
  ],
  "pk_mappings": [
    {
      "pk_columns": [
        "issue_id"
      ],
      "data_columns": [
        "title",
        "description"
      ]
    },
    {
      "pk_columns": [
        "author_id"
      ],
      "data_columns": [
        "author"
      ]
    }
  ]
}
```



