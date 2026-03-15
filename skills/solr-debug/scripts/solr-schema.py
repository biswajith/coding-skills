#!/usr/bin/env python3
"""
Solr schema introspection for db-context skill.
Reads SOLR_URL from env, application.properties, or application.yml.
No extra dependencies required — uses urllib from stdlib.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from pathlib import Path


def find_solr_url():
    # 1. env var
    url = os.getenv("SOLR_URL")
    if url:
        return url.rstrip("/")

    # 2. application.properties
    props_path = Path("src/main/resources/application.properties")
    if props_path.exists():
        with open(props_path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("spring.data.solr.host") or line.startswith("solr.url") or line.startswith("solr.host"):
                    _, _, v = line.partition("=")
                    return v.strip().rstrip("/")

    # 3. application.yml
    for yml_path in [Path("src/main/resources/application.yml"), Path("src/main/resources/application.yaml")]:
        if yml_path.exists():
            with open(yml_path) as f:
                content = f.read()
            m = re.search(r"host:\s*(http[^\s]+)", content)
            if m:
                return m.group(1).rstrip("/")

    return "http://localhost:8983/solr"


def fetch_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"ERROR connecting to Solr at {url}: {e}")
        sys.exit(1)


def introspect(solr_url: str):
    print(f"\n=== Solr Schema: {solr_url} ===\n")

    # List cores
    admin_data = fetch_json(f"{solr_url}/admin/cores?action=STATUS&wt=json")
    cores = admin_data.get("status", {})

    if not cores:
        # Try collections API (SolrCloud)
        try:
            coll_data = fetch_json(f"{solr_url}/admin/collections?action=LIST&wt=json")
            core_names = coll_data.get("collections", [])
            cores = {c: {} for c in core_names}
        except SystemExit:
            print("No cores or collections found.")
            return

    print(f"Cores/Collections ({len(cores)}):")
    for name, info in cores.items():
        index = info.get("index", {})
        num_docs = index.get("numDocs", "?")
        size = index.get("sizeInBytes", 0)
        size_mb = f"{size / (1024*1024):.1f} MB" if isinstance(size, int) else "?"
        print(f"  {name:40s}  {num_docs:>8} docs  {size_mb}")

    # Schema per core
    for core_name in cores:
        print(f"\n--- Schema: {core_name} ---")
        schema_data = fetch_json(f"{solr_url}/{core_name}/schema?wt=json")
        schema = schema_data.get("schema", {})

        # Fields
        fields = schema.get("fields", [])
        print(f"\n  Fields ({len(fields)}):")
        for f in sorted(fields, key=lambda x: x["name"]):
            flags = []
            if f.get("indexed", True): flags.append("indexed")
            if f.get("stored", True): flags.append("stored")
            if f.get("multiValued"): flags.append("multiValued")
            if f.get("required"): flags.append("required")
            if f.get("docValues"): flags.append("docValues")
            flag_str = f"  [{', '.join(flags)}]" if flags else ""
            print(f"    {f['name']:35s} {f['type']:25s}{flag_str}")

        # Dynamic fields
        dynamic_fields = schema.get("dynamicFields", [])
        if dynamic_fields:
            print(f"\n  Dynamic Fields ({len(dynamic_fields)}):")
            for df in dynamic_fields:
                print(f"    {df['name']:35s} {df['type']}")

        # Copy fields
        copy_fields = schema.get("copyFields", [])
        if copy_fields:
            print(f"\n  Copy Fields ({len(copy_fields)}):")
            for cf in copy_fields:
                print(f"    {cf['source']:35s} → {cf['dest']}")

        # Unique key
        unique_key = schema.get("uniqueKey")
        if unique_key:
            print(f"\n  Unique Key: {unique_key}")

    print("\n=== End Solr Schema ===\n")


if __name__ == "__main__":
    solr_url = find_solr_url()
    introspect(solr_url)
