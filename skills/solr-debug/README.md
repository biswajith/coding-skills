# solr-debug — Setup Guide

## Requirements

Python 3.8+ — no extra packages needed. The scripts use only the standard library (`urllib`, `json`).

## Connection config

The skill auto-detects the Solr URL in this order:

1. **`.claude/STACK.md`** in your project — recommended. Add the `Solr Connection` section:
   ```
   SOLR_URL: http://localhost:8983/solr
   ```

2. **`src/main/resources/application.properties`** — reads `spring.data.solr.host` or `solr.url`

3. **`src/main/resources/application.yml`** — reads the same keys

4. **Environment variable** — `SOLR_URL`

5. **Default** — `http://localhost:8983/solr`

## Solr authentication

If your Solr instance requires basic auth, set:

```bash
export SOLR_USER=your_user
export SOLR_PASSWORD=your_password
```

Then update `scripts/solr-schema.py` and `scripts/solr-query.py` to pass credentials — or configure a Solr `security.json` that allows the connecting host.

For SolrCloud, the URL should point to any node; collection listing uses the Collections API automatically.

## What the scripts do

| Script | Purpose |
|---|---|
| `scripts/solr-schema.py` | All cores/collections — fields, dynamic fields, copy fields, doc counts, index size |
| `scripts/solr-query.py --core <name> --query "q"` | Run a query against a core |
| `scripts/solr-query.py --core <name> --query "q" --debug` | Run with `debugQuery=true` — shows parse tree and per-doc score explanation |
| `scripts/solr-query.py --core <name> --analyze --field <f> --text "term"` | Show full tokenization pipeline for a field — why a match succeeds or fails |
| `scripts/solr-query.py --core <name> --get-doc <id>` | Fetch a specific document by ID |
| `scripts/solr-query.py --core <name> --stats` | Core stats: doc count, segment count, last modified, pending deletes |

## Common debug scenarios

| Problem | Command to run |
|---|---|
| Search returns no results | `--query "field:value" --debug` to see parse tree |
| Partial match not working | `--analyze --field <f> --text "term"` to see tokenization |
| Document missing after indexing | `--get-doc <id>` to check if it's actually there |
| Sorting or facets broken | Check `docValues` in schema via `solr-schema.py` |
| Spring `@Query` not matching | `--query` the raw Solr query from the annotation |

## Solr Admin UI alternative

If you prefer the browser: `http://localhost:8983/solr/#/<core>/query` gives the same query debug UI. The skill scripts are useful when you want the agent to read and act on the output directly.

## Usage

Point the agent at a problem and invoke the skill:

```
/solr-debug

My ProductRepository.findByNameContaining("widget") returns no results,
but I can see documents in the index. Here is the repository:
[paste or reference the file]
```

The agent will connect, inspect the schema, run the query with debug output, and diagnose the mismatch.
