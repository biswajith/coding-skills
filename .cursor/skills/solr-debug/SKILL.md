---
name: solr-debug
description: Connects to Solr, introspects core schema and stats, runs diagnostic queries, and debugs a specific search or indexing problem the developer points at. Use when debugging a Solr search issue, investigating why documents are not found, checking field values, diagnosing query relevance, or when the user points at a Solr repository class or search query.
disable-model-invocation: true
allowed-tools: Bash(python3 *), Bash(curl *)
---

# Solr Debugger

Connect to Solr and actively debug the search or indexing problem the developer points at.

## Step 1: Understand the problem

The developer will point you at one of:
- A Spring Data Solr repository or `SolrClient` query that returns wrong results
- A search that returns no results when results are expected
- An indexing problem (documents not appearing, wrong field values)
- A relevance/ranking issue (wrong documents ranked first)
- A field type or schema mismatch error

Read the referenced code or error before connecting to Solr.

## Step 2: Connect and load schema

Run the schema introspection script:

```bash
python3 ~/.claude/skills/solr-debug/scripts/solr-schema.py
```

Connection URL is auto-detected from (in order):
1. `.claude/STACK.md`
2. `src/main/resources/application.properties` (`spring.data.solr.host` or `solr.url`)
3. `src/main/resources/application.yml`
4. Env var: `SOLR_URL`
5. Default: `http://localhost:8983/solr`

## Step 3: Debug the problem

### No results / wrong results
Test the exact query against Solr directly to isolate whether the issue is in the query or the data:

```bash
python3 ~/.claude/skills/solr-debug/scripts/solr-query.py \
  --core <core_name> \
  --query "field:value" \
  --debug
```

The `--debug` flag fetches Solr's `debugQuery=true` output, which shows:
- How the query was parsed
- Which analyzer was applied to each field
- Per-document score explanation

### Field type mismatch
Check what the field type actually does to the search terms:

```bash
python3 ~/.claude/skills/solr-debug/scripts/solr-query.py \
  --core <core_name> \
  --analyze --field <field_name> --text "<search term>"
```

This calls the Solr Analysis API and shows tokenization/analysis output.

### Document not indexed / wrong field values
Fetch a specific document by ID:

```bash
python3 ~/.claude/skills/solr-debug/scripts/solr-query.py \
  --core <core_name> \
  --get-doc <id>
```

### Index health check
Check core stats, last commit time, pending deletes:

```bash
python3 ~/.claude/skills/solr-debug/scripts/solr-schema.py --stats
```

### Schema vs code mismatch
Compare the Solr schema fields against field names used in the Spring repository or `@SolrDocument` class:
- Check field names match exactly (case-sensitive)
- Check `multiValued` matches Java collection vs scalar
- Check `stored=false` fields cannot be retrieved — only searched
- Check `indexed=false` fields cannot be searched — only stored

## Step 4: Common Solr problems and what to check

| Symptom | What to investigate |
|---|---|
| No results for a query | Field analyzer, query parser, field name typo |
| Partial match not working | Field not using `text_general` or similar analyzed type |
| Exact match returning nothing | Analyzer lowercasing / tokenizing the field |
| Sorting broken | Field not `docValues=true` |
| Facets returning nothing | Field not `indexed=true` or wrong type |
| Document missing after index | Commit not called (soft vs hard commit) |
| Score unexpectedly low | IDF across small corpus, field boost missing |
| Spring `@Query` not working | SolrJ query syntax vs Solr query parser mismatch |

## Step 5: Report findings

```
## Solr Debug Report

**Problem:** <what the developer reported>
**Core:** <core_name>
**Query tested:** <query string>

### Schema findings
<Field type issues, mismatches with Java code>

### Query analysis
<How Solr parsed the query, analyzer output>

### Document inspection
<What the actual indexed data looks like>

### Root cause
<Your diagnosis>

### Fix
<Specific schema change, query fix, or code change>
```

## Additional resources

- [scripts/solr-schema.py](scripts/solr-schema.py) — core and schema introspection
- [scripts/solr-query.py](scripts/solr-query.py) — query runner, debug, and analysis helper
