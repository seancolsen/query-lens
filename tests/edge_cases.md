# Edge cases

## CTE with a forward reference

```json
{
  "database_structure": 'issue_tracker_schema.json'
}
```

```sql
with recursive
b as (select x from a),
a as (select 1 as x, 2 as y)
select * from b;
```

```json
{
  "result_columns": [
    {
      "classification": "data",
      "type": "integer",
      "name": "x"
    }
  ]
}
```

## Reference to a table with the same name as a CTE

In this query, `select * from teams` refers to the **table** `teams` in the database, not the **CTE** `teams` defined in the query.

```json
{
  "database_structure": 'issue_tracker_schema.json'
}
```

```sql
with
a as (select * from teams),
teams as (select 'THIS IS NEVER USED!' as n)
select * from a;
```

```json
{
  "result_columns": [
    {
      "classification": "primary_key",
      "type": "integer",
      "name": "id",
      "table": {
        "name": "teams",
        "oid": 9
      },
      "column": {
        "name": "id",
        "attnum": 1
      },
    },
    {
      "classification": "data",
      "type": "text",
      "name": "name",
      "table": {
        "name": "teams",
        "oid": 9
      },
      "column": {
        "name": "id",
        "attnum": 1
      },
      "primary_key_lookup_names": [ "id" ]
    }
  ]
}
```

## Forward reference to a CTE that shadows a table

In this query, `select * from teams` refers to the **CTE** `teams` defined in the query, not the **table** `teams` in the database.

```json
{
  "database_structure": 'issue_tracker_schema.json'
}
```

```sql
with recursive
a as (select * from teams),
teams as (select 'USED!' as n)
select * from a;
```

```json
{
  "result_columns": [
    {
      "classification": "constant",
      "type": "text",
      "name": "n",
    }
  ]
}
```

## Inner CTE referencing an outer CTE

```json
{
  "database_structure": 'issue_tracker_schema.json'
}
```

```sql
with
a(n) as (select 7),
b as (with c as (select * from a) select * from c)
select * from b;
```




