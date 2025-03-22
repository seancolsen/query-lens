# Playground

## Case 0

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
{
  "result_columns": [],
  "pk_mappings": []
}
```