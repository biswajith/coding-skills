# mysql-debug — Setup Guide

## Requirements

Python 3.8+ and two packages:

```bash
pip install mysql-connector-python pyyaml
```

## Connection config

The skill auto-detects connection details in this order:

1. **`.claude/STACK.md`** in your project — recommended. Add the `Database Connection` section:
   ```
   DB_HOST: localhost
   DB_PORT: 3306
   DB_NAME: your_database
   DB_USER: your_user
   DB_PASSWORD:
   ```
   Leave `DB_PASSWORD` blank in STACK.md — set it via env var instead.

2. **`src/main/resources/application.properties`** — reads `spring.datasource.url`, `spring.datasource.username`, `spring.datasource.password`

3. **`src/main/resources/application.yml`** — reads the same Spring datasource keys

4. **Environment variables** — `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

## Recommended setup (keep credentials out of files)

```bash
export DB_PASSWORD=your_password
```

Add to your shell profile (`~/.zshrc` or `~/.bashrc`) or use a `.env` file that is gitignored.

## What the scripts do

| Script | Purpose |
|---|---|
| `scripts/mysql-schema.py` | Full schema dump — all tables, columns, types, indexes, foreign keys, row counts |
| `scripts/mysql-query.py --query "SQL"` | Run any SELECT query |
| `scripts/mysql-query.py --explain "SQL"` | EXPLAIN + automatic problem flagging (full scans, filesort, missing indexes) |
| `scripts/mysql-query.py --slow-queries` | Top 20 slow queries from `performance_schema` |
| `scripts/mysql-query.py --table <name>` | Detailed columns, indexes, and FKs for one table |

## Permissions needed

The database user needs at minimum:
```sql
GRANT SELECT ON your_database.* TO 'your_user'@'%';
GRANT SELECT ON information_schema.* TO 'your_user'@'%';
GRANT SELECT ON performance_schema.* TO 'your_user'@'%';  -- for slow query analysis
```

## Usage

Point the agent at a problem and invoke the skill:

```
/mysql-debug

I'm getting a LazyInitializationException in OrderService.java:45.
Here is the entity: [paste or reference the file]
```

The agent will connect, inspect the relevant tables, and diagnose the issue.
