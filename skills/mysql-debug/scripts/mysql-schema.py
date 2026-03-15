#!/usr/bin/env python3
"""
MySQL schema introspection for db-context skill.
Reads connection from env vars, application.properties, or application.yml.
Requires: pip install mysql-connector-python pyyaml
"""

import os
import re
import sys
from pathlib import Path


def load_from_stack_md():
    stack_path = Path(".claude/STACK.md")
    if not stack_path.exists():
        return None
    text = stack_path.read_text()
    def extract(key):
        m = re.search(rf"\*\*{key}:\*\*\s*([^\n]+)", text)
        if not m:
            return None
        v = m.group(1).strip()
        return None if not v or v.startswith("(") else v

    host = extract("DB_HOST")
    port = extract("DB_PORT")
    db   = extract("DB_NAME")
    user = extract("DB_USER")
    pwd  = extract("DB_PASSWORD")
    if host or db or user:
        return {
            "host": host or "localhost",
            "port": int(port) if port and port.isdigit() else 3306,
            "database": db,
            "user": user,
            "password": pwd or os.getenv("DB_PASSWORD"),
        }
    return None


def load_from_env():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME") or os.getenv("DB_DATABASE"),
        "user": os.getenv("DB_USER") or os.getenv("DB_USERNAME"),
        "password": os.getenv("DB_PASSWORD"),
    }


def load_from_properties(path: Path):
    props = {}
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                props[k.strip()] = v.strip()

    url = props.get("spring.datasource.url", "")
    # jdbc:mysql://host:port/dbname
    m = re.match(r"jdbc:mysql://([^:/]+):?(\d+)?/([^?]+)", url)
    host, port, db = (m.group(1), m.group(2) or "3306", m.group(3)) if m else (None, "3306", None)

    return {
        "host": host or "localhost",
        "port": int(port),
        "database": db,
        "user": props.get("spring.datasource.username"),
        "password": props.get("spring.datasource.password"),
    }


def load_from_yaml(path: Path):
    try:
        import yaml
    except ImportError:
        return None
    with open(path) as f:
        data = yaml.safe_load(f)
    ds = (data or {}).get("spring", {}).get("datasource", {})
    url = ds.get("url", "")
    m = re.match(r"jdbc:mysql://([^:/]+):?(\d+)?/([^?]+)", url)
    host, port, db = (m.group(1), m.group(2) or "3306", m.group(3)) if m else (None, "3306", None)
    return {
        "host": host or "localhost",
        "port": int(port),
        "database": db,
        "user": ds.get("username"),
        "password": ds.get("password"),
    }


def find_config():
    config = load_from_stack_md()
    if config:
        return config
    for p in [
        Path("src/main/resources/application.properties"),
        Path("src/main/resources/application.yml"),
        Path("src/main/resources/application.yaml"),
    ]:
        if p.exists():
            return load_from_properties(p) if p.suffix == ".properties" else load_from_yaml(p)
    return load_from_env()


def introspect(config: dict):
    try:
        import mysql.connector
    except ImportError:
        print("ERROR: mysql-connector-python not installed. Run: pip install mysql-connector-python")
        sys.exit(1)

    if not config.get("database"):
        print("ERROR: Could not determine database name from config. Set DB_NAME env var or check application.properties.")
        sys.exit(1)

    conn = mysql.connector.connect(
        host=config["host"],
        port=config["port"],
        database=config["database"],
        user=config["user"],
        password=config["password"],
        connection_timeout=10,
    )
    cursor = conn.cursor(dictionary=True)

    print(f"\n=== MySQL Schema: {config['database']} @ {config['host']}:{config['port']} ===\n")

    # Tables with row counts
    cursor.execute("""
        SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH, TABLE_COMMENT
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
    """, (config["database"],))
    tables = cursor.fetchall()
    print(f"Tables ({len(tables)}):")
    for t in tables:
        size_kb = ((t["DATA_LENGTH"] or 0) + (t["INDEX_LENGTH"] or 0)) // 1024
        print(f"  {t['TABLE_NAME']:40s} ~{t['TABLE_ROWS'] or 0:>8} rows  {size_kb:>6} KB  {t['TABLE_COMMENT'] or ''}")

    # Columns per table
    print("\n--- Column Details ---")
    for t in tables:
        tname = t["TABLE_NAME"]
        cursor.execute("""
            SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
        """, (config["database"], tname))
        cols = cursor.fetchall()
        print(f"\n  {tname}")
        for c in cols:
            flags = []
            if c["COLUMN_KEY"] == "PRI": flags.append("PK")
            if c["COLUMN_KEY"] == "UNI": flags.append("UNIQUE")
            if c["COLUMN_KEY"] == "MUL": flags.append("INDEX")
            if c["IS_NULLABLE"] == "NO": flags.append("NOT NULL")
            if c["EXTRA"]: flags.append(c["EXTRA"])
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            print(f"    {c['COLUMN_NAME']:35s} {c['COLUMN_TYPE']:25s}{flag_str}  {c['COLUMN_COMMENT'] or ''}")

    # Foreign keys
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME, CONSTRAINT_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND REFERENCED_TABLE_NAME IS NOT NULL
        ORDER BY TABLE_NAME
    """, (config["database"],))
    fks = cursor.fetchall()
    if fks:
        print("\n--- Foreign Keys ---")
        for fk in fks:
            print(f"  {fk['TABLE_NAME']}.{fk['COLUMN_NAME']} → {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")

    # Indexes
    cursor.execute("""
        SELECT TABLE_NAME, INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLUMNS, NON_UNIQUE
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s
        GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE
        ORDER BY TABLE_NAME, INDEX_NAME
    """, (config["database"],))
    indexes = cursor.fetchall()
    if indexes:
        print("\n--- Indexes ---")
        for idx in indexes:
            uq = "" if idx["NON_UNIQUE"] else " [UNIQUE]"
            print(f"  {idx['TABLE_NAME']:35s} {idx['INDEX_NAME']:30s} ({idx['COLUMNS']}){uq}")

    cursor.close()
    conn.close()
    print("\n=== End MySQL Schema ===\n")


if __name__ == "__main__":
    config = find_config()
    introspect(config)
