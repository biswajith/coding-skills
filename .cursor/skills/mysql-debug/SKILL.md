---
name: mysql-debug
description: Connects to MySQL, introspects schema, runs diagnostic queries, and debugs a specific code or data problem the developer points at. Use when debugging a database issue, investigating a query, checking data state, diagnosing a Hibernate/JPA problem, or when the user says "check the database", "why is this query slow", "what does the data look like", or points at a Java entity or repository class.
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(mysql *)
---

# MySQL Debugger

Connect to MySQL, understand the schema, and actively debug the problem the developer points at.

## Step 1: Understand the problem

The developer will point you at one of:
- A Java entity or repository class with a suspected issue
- A specific query or endpoint that is misbehaving
- An error message or stack trace
- A data integrity question ("why does this record have X value?")
- A performance complaint ("this query is slow")

Read the referenced code or error before connecting to the database.

## Step 2: Connect and load schema

Run the introspection script to understand the relevant tables:

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-schema.py
```

Connection config is auto-detected from (in order):
1. `.claude/STACK.md`
2. `src/main/resources/application.properties`
3. `src/main/resources/application.yml`
4. Env vars: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

If connection fails, report the exact error and ask the user to verify credentials.

**Requires:** `pip install mysql-connector-python pyyaml`

## Step 3: Debug the problem

Based on the problem type, run targeted diagnostics:

### Hibernate / JPA mapping issues
- Compare `@Entity` fields against actual table columns (types, nullability, names)
- Check `@JoinColumn` foreign key names against real FK constraints
- Identify `@OneToMany` without indexes on the FK column → N+1 risk
- Check `@Column(length=X)` matches actual column size

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-schema.py --table <table_name>
```

### Query / performance issues
Run the problematic query with `EXPLAIN` and `EXPLAIN ANALYZE`:

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-query.py --explain "<SQL>"
```

Look for:
- Full table scans (`type: ALL`) on large tables
- Missing indexes on JOIN or WHERE columns
- Filesort or temporary table in `Extra`
- Row estimates vs actual rows

### Data state investigation
Run targeted SELECT queries to inspect actual data:

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-query.py --query "<SQL>"
```

### Constraint / integrity issues
- Check FK violations
- Check unique constraint conflicts
- Inspect trigger definitions if relevant

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-query.py --query "SELECT * FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA = DATABASE()"
```

### Slow query investigation
Check recent slow queries from `performance_schema`:

```bash
python3 ~/.claude/skills/mysql-debug/scripts/mysql-query.py --slow-queries
```

## Step 4: Report findings

Structure your findings as:

```
## MySQL Debug Report

**Problem:** <what the developer reported>
**Tables involved:** <list>

### Schema findings
<Any mismatch between code and schema>

### Query analysis
<EXPLAIN output interpretation>

### Data findings
<What the data actually shows>

### Root cause
<Your diagnosis>

### Fix
<Specific code or SQL change to resolve the issue>
```

## Additional resources

- [scripts/mysql-schema.py](scripts/mysql-schema.py) — schema introspection
- [scripts/mysql-query.py](scripts/mysql-query.py) — query runner and EXPLAIN helper
