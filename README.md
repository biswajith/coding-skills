# Claude / Cursor Skills

Reusable agent skills for Java Spring development with OpenAI, Solr, and MySQL.

## Skills

| Skill | Invoke | Purpose |
|---|---|---|
| `architect-plan` | `/architect-plan` | Sr. Architect persona — produces a structured feature plan doc |
| `tdd-workflow` | `/tdd-workflow <plan-name>` | Red-Green-Refactor TDD cycle driven by approved plan |
| `code-review` | `/code-review <plan-name>` | Code review cross-checked against plan and STACK.md |
| `plan-adherence` | `/plan-adherence <plan-name>` | Scores how faithfully code matches the approved plan |
| `github-review-comments` | `/github-review-comments <PR#>` | Fetches PR review comments and produces an action plan |
| `mysql-debug` | `/mysql-debug` | Connects to MySQL, inspects schema, debugs queries and entity issues |
| `solr-debug` | `/solr-debug` | Connects to Solr, inspects schema, debugs search and indexing issues |
| `jellyfish-insights` | `/jellyfish-insights` | Surfaces DORA metrics and delivery insights from Jellyfish |

## Setup per project

1. Copy `STACK.md` template into your project:
   ```bash
   cp skills/architect-plan/STACK-TEMPLATE.md <your-project>/.claude/STACK.md
   ```
2. Fill in your stack details — all skills read from this file.
3. Add `.claude/STACK.md` to `.gitignore` if it contains credentials.

## Workflow

```
/architect-plan          → produces .claude/plans/<feature>.md
  ↓ (team reviews & approves)
/tdd-workflow <feature>  → implements via Red-Green-Refactor
  ↓
/plan-adherence <feature> → scores code vs plan (need ≥80% to PR)
  ↓
/code-review <feature>   → full quality review
  ↓
/github-review-comments <PR#> → address reviewer feedback
```
