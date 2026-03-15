#!/usr/bin/env python3
"""
MySQL query runner and EXPLAIN helper for mysql-debug skill.
Usage:
  python3 mysql-query.py --query "SELECT ..."
  python3 mysql-query.py --explain "SELECT ..."
  python3 mysql-query.py --slow-queries
  python3 mysql-query.py --table <table_name>
Requires: pip install mysql-connector-python pyyaml
"""

import sys
import os
import re
import argparse
from pathlib import Path


def load_config():
    # Reuse same config detection as mysql-schema.py
    sys.path.insert(0, str(Path(__file__).parent))
    from mysql_schema import find_config
    return find_config()


def get_connection(config):
    try:
        import mysql.connector
    except ImportError:
        print("ERROR: pip install mysql-connector-python")
        sys.exit(1)
    return mysql.connector.connect(
        host=config["host"], port=config["port"],
        database=config["database"], user=config["user"],
        password=config["password"], connection_timeout=10,
    )


def run_query(config, sql: str):
    conn = get_connection(config)
    cursor = conn.cursor(dictionary=True)
    print(f"\n>> {sql}\n")
    cursor.execute(sql)
    rows = cursor.fetchall()
    if not rows:
        print("(no rows returned)")
    else:
        # Print as aligned table
        keys = list(rows[0].keys())
        widths = {k: max(len(str(k)), max(len(str(r.get(k, ""))) for r in rows)) for k in keys}
        header = "  ".join(str(k).ljust(widths[k]) for k in keys)
        print(header)
        print("-" * len(header))
        for row in rows:
            print("  ".join(str(row.get(k, "")).ljust(widths[k]) for k in keys))
    print(f"\n({len(rows)} row(s))")
    cursor.close()
    conn.close()


def run_explain(config, sql: str):
    conn = get_connection(config)
    cursor = conn.cursor(dictionary=True)

    print(f"\n=== EXPLAIN ===\n>> {sql}\n")
    cursor.execute(f"EXPLAIN {sql}")
    rows = cursor.fetchall()
    keys = list(rows[0].keys()) if rows else []
    if keys:
        widths = {k: max(len(str(k)), max(len(str(r.get(k, "") or "")) for r in rows)) for k in keys}
        print("  ".join(str(k).ljust(widths[k]) for k in keys))
        print("-" * sum(widths.values()))
        for row in rows:
            print("  ".join(str(row.get(k, "") or "").ljust(widths[k]) for k in keys))

    # Flag problems
    print("\n=== Analysis ===")
    for row in rows:
        table = row.get("table", "")
        typ = row.get("type", "")
        extra = row.get("Extra", "") or ""
        rows_est = row.get("rows", 0) or 0
        key = row.get("key")

        if typ == "ALL":
            print(f"⚠️  FULL TABLE SCAN on `{table}` (~{rows_est} rows) — consider adding an index")
        if "Using filesort" in extra:
            print(f"⚠️  FILESORT on `{table}` — ORDER BY cannot use an index")
        if "Using temporary" in extra:
            print(f"⚠️  TEMPORARY TABLE on `{table}` — GROUP BY or DISTINCT is expensive")
        if typ in ("ALL", "index") and not key:
            print(f"⚠️  No index used on `{table}`")
        if typ in ("ref", "eq_ref", "const"):
            print(f"✅  Index used on `{table}`: {key}")

    # Try EXPLAIN ANALYZE (MySQL 8+)
    try:
        cursor.execute(f"EXPLAIN ANALYZE {sql}")
        analyze = cursor.fetchall()
        print("\n=== EXPLAIN ANALYZE ===")
        for row in analyze:
            print(list(row.values())[0])
    except Exception:
        pass  # MySQL < 8 doesn't support EXPLAIN ANALYZE

    cursor.close()
    conn.close()


def run_slow_queries(config):
    conn = get_connection(config)
    cursor = conn.cursor(dictionary=True)
    print("\n=== Top 20 Slow Queries (performance_schema) ===\n")
    try:
        cursor.execute("""
            SELECT DIGEST_TEXT, COUNT_STAR, AVG_TIMER_WAIT/1000000000 AS avg_ms,
                   MAX_TIMER_WAIT/1000000000 AS max_ms, SUM_ROWS_EXAMINED, SUM_ROWS_SENT
            FROM performance_schema.events_statements_summary_by_digest
            WHERE DIGEST_TEXT IS NOT NULL
            ORDER BY AVG_TIMER_WAIT DESC
            LIMIT 20
        """)
        rows = cursor.fetchall()
        for i, row in enumerate(rows, 1):
            print(f"{i:2}. avg={row['avg_ms']:.1f}ms  max={row['max_ms']:.1f}ms  "
                  f"calls={row['COUNT_STAR']}  rows_examined={row['SUM_ROWS_EXAMINED']}")
            print(f"    {(row['DIGEST_TEXT'] or '')[:120]}")
            print()
    except Exception as e:
        print(f"performance_schema not available: {e}")
        print("Try: SET GLOBAL performance_schema = ON;")
    cursor.close()
    conn.close()


def table_detail(config, table_name: str):
    conn = get_connection(config)
    cursor = conn.cursor(dictionary=True)
    db = config["database"]

    print(f"\n=== Table: {table_name} ===\n")

    cursor.execute("""
        SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA, COLUMN_COMMENT
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION
    """, (db, table_name))
    cols = cursor.fetchall()
    print("Columns:")
    for c in cols:
        flags = []
        if c["COLUMN_KEY"] == "PRI": flags.append("PK")
        if c["COLUMN_KEY"] == "UNI": flags.append("UNIQUE")
        if c["COLUMN_KEY"] == "MUL": flags.append("INDEX")
        if c["IS_NULLABLE"] == "NO": flags.append("NOT NULL")
        if c["EXTRA"]: flags.append(c["EXTRA"])
        print(f"  {c['COLUMN_NAME']:35s} {c['COLUMN_TYPE']:25s} {', '.join(flags)}")

    cursor.execute("""
        SELECT INDEX_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) AS COLS, NON_UNIQUE
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        GROUP BY INDEX_NAME, NON_UNIQUE
    """, (db, table_name))
    indexes = cursor.fetchall()
    if indexes:
        print("\nIndexes:")
        for idx in indexes:
            uq = "" if idx["NON_UNIQUE"] else " [UNIQUE]"
            print(f"  {idx['INDEX_NAME']:30s} ({idx['COLS']}){uq}")

    cursor.execute("""
        SELECT COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
        FROM information_schema.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND REFERENCED_TABLE_NAME IS NOT NULL
    """, (db, table_name))
    fks = cursor.fetchall()
    if fks:
        print("\nForeign Keys:")
        for fk in fks:
            print(f"  {fk['COLUMN_NAME']} → {fk['REFERENCED_TABLE_NAME']}.{fk['REFERENCED_COLUMN_NAME']}")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Run a SELECT query")
    parser.add_argument("--explain", help="Run EXPLAIN + analysis on a query")
    parser.add_argument("--slow-queries", action="store_true", help="Show slow query digest")
    parser.add_argument("--table", help="Show detailed info for a specific table")
    args = parser.parse_args()

    config = load_config()

    if args.query:
        run_query(config, args.query)
    elif args.explain:
        run_explain(config, args.explain)
    elif args.slow_queries:
        run_slow_queries(config)
    elif args.table:
        table_detail(config, args.table)
    else:
        parser.print_help()
