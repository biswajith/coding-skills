#!/usr/bin/env python3
"""
Solr query runner and debug helper for solr-debug skill.
Usage:
  python3 solr-query.py --core <name> --query "field:value" [--debug] [--rows 10]
  python3 solr-query.py --core <name> --get-doc <id>
  python3 solr-query.py --core <name> --analyze --field <field> --text "search term"
  python3 solr-query.py --core <name> --stats
No extra dependencies — uses stdlib urllib only.
"""

import os
import sys
import json
import re
import argparse
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path


def find_solr_url() -> str:
    # 1. .claude/connections.env
    env_path = Path(".claude/connections.env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "SOLR_URL" and v.strip():
                return v.strip().rstrip("/")

    # 2. env var
    url = os.getenv("SOLR_URL")
    if url:
        return url.rstrip("/")

    # 3. application.properties
    props_path = Path("src/main/resources/application.properties")
    if props_path.exists():
        with open(props_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith(("spring.data.solr.host", "solr.url", "solr.host")) and "=" in line:
                    _, _, v = line.partition("=")
                    return v.strip().rstrip("/")

    # 4. application.yml / application.yaml
    for yml in [Path("src/main/resources/application.yml"), Path("src/main/resources/application.yaml")]:
        if yml.exists():
            with open(yml) as f:
                content = f.read()
            m = re.search(r"host:\s*(http[^\s\n]+)", content)
            if m:
                return m.group(1).rstrip("/")

    return "http://localhost:8983/solr"


def fetch(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} from Solr: {body[:500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Cannot connect to Solr: {e}")
        sys.exit(1)


def run_query(solr_url: str, core: str, query: str, rows: int, debug: bool, fl: str = None):
    params = {
        "q": query,
        "rows": str(rows),
        "wt": "json",
        "indent": "true",
    }
    if debug:
        params["debugQuery"] = "true"
        params["debug.explain.structured"] = "true"
    if fl:
        params["fl"] = fl

    url = f"{solr_url}/{core}/select?{urllib.parse.urlencode(params)}"
    print(f"\n>> GET {url}\n")
    data = fetch(url)

    response = data.get("response", {})
    num_found = response.get("numFound", 0)
    docs = response.get("docs", [])

    print(f"Found: {num_found} documents  (showing {len(docs)})\n")

    for i, doc in enumerate(docs, 1):
        print(f"--- Doc {i} ---")
        for k, v in doc.items():
            print(f"  {k}: {v}")
        print()

    if debug and "debug" in data:
        dbg = data["debug"]
        print("=== Query Parse Debug ===")
        print(f"  parsedquery: {dbg.get('parsedquery', '')}")
        print(f"  parsedquery_toString: {dbg.get('parsedquery_toString', '')}")

        explain = dbg.get("explain", {})
        if explain:
            print("\n=== Score Explanations ===")
            for doc_id, explanation in list(explain.items())[:5]:
                print(f"\n  Doc: {doc_id}")
                for line in str(explanation).split("\n")[:15]:
                    print(f"    {line}")

        timing = dbg.get("timing", {})
        if timing:
            print(f"\n=== Timing ===")
            print(f"  Total: {timing.get('time', '?')}ms")


def get_doc(solr_url: str, core: str, doc_id: str):
    params = {"q": f"id:{urllib.parse.quote(doc_id)}", "wt": "json", "rows": "1"}
    url = f"{solr_url}/{core}/select?{urllib.parse.urlencode(params)}"
    data = fetch(url)
    docs = data.get("response", {}).get("docs", [])
    if not docs:
        print(f"No document found with id={doc_id}")
        return
    print(f"\n=== Document: {doc_id} ===\n")
    for k, v in docs[0].items():
        print(f"  {k:35s}: {v}")


def analyze_field(solr_url: str, core: str, field: str, text: str):
    params = {
        "analysis.fieldname": field,
        "analysis.fieldvalue": text,
        "wt": "json",
    }
    url = f"{solr_url}/{core}/analysis/field?{urllib.parse.urlencode(params)}"
    print(f"\n=== Field Analysis: field={field}, text='{text}' ===\n")
    data = fetch(url)

    analysis = data.get("analysis", {}).get("field_names", {}).get(field, {})
    for stage_name, tokens in analysis.items():
        if isinstance(tokens, list):
            token_strs = [t.get("text", str(t)) for t in tokens if isinstance(t, dict)]
            print(f"  {stage_name}: {token_strs}")
        else:
            print(f"  {stage_name}: {tokens}")

    print("\nWhat this means:")
    print("  - The final token list is what Solr indexes / matches against")
    print("  - If your search term doesn't produce the same tokens → no match")


def core_stats(solr_url: str, core: str):
    url = f"{solr_url}/{core}/admin/luke?wt=json&numTerms=0"
    print(f"\n=== Core Stats: {core} ===\n")
    data = fetch(url)
    info = data.get("index", {})
    print(f"  numDocs:        {info.get('numDocs', '?')}")
    print(f"  maxDoc:         {info.get('maxDoc', '?')}")
    print(f"  deletedDocs:    {info.get('deletedDocs', '?')}")
    print(f"  version:        {info.get('version', '?')}")
    print(f"  segmentCount:   {info.get('segmentCount', '?')}")
    print(f"  hasDeletions:   {info.get('hasDeletions', '?')}")
    print(f"  directory:      {info.get('directory', '?')}")
    last_modified = info.get("lastModified")
    if last_modified:
        print(f"  lastModified:   {last_modified}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solr debug query tool")
    parser.add_argument("--core", required=True, help="Solr core or collection name")
    parser.add_argument("--query", help="Solr query string (q param)")
    parser.add_argument("--rows", type=int, default=10, help="Number of results (default 10)")
    parser.add_argument("--debug", action="store_true", help="Enable debugQuery=true")
    parser.add_argument("--fl", help="Field list to return (comma-separated)")
    parser.add_argument("--get-doc", metavar="ID", help="Fetch a specific document by ID")
    parser.add_argument("--analyze", action="store_true", help="Analyze a field's tokenization")
    parser.add_argument("--field", help="Field name for --analyze")
    parser.add_argument("--text", help="Text to analyze for --analyze")
    parser.add_argument("--stats", action="store_true", help="Show core stats")
    args = parser.parse_args()

    solr_url = find_solr_url()

    if args.query:
        run_query(solr_url, args.core, args.query, args.rows, args.debug, args.fl)
    elif args.get_doc:
        get_doc(solr_url, args.core, args.get_doc)
    elif args.analyze:
        if not args.field or not args.text:
            print("--analyze requires --field and --text")
            sys.exit(1)
        analyze_field(solr_url, args.core, args.field, args.text)
    elif args.stats:
        core_stats(solr_url, args.core)
    else:
        parser.print_help()
