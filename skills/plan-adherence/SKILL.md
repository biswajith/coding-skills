---
name: plan-adherence
description: Measures how faithfully the current codebase or changed files match an approved feature plan. Produces a scored adherence report with deviations, gaps, and a pass/fail verdict. Use when validating implementation against a plan, before a PR, or when the user asks "does the code match the plan", "plan compliance", or "adherence check".
disable-model-invocation: true
---

# Plan Adherence Check

Measure how faithfully the code matches an approved plan document. Produces a scored report and explicit list of deviations.

## Step 1: Load context

1. Read `.claude/STACK.md` — defines ORM, repositories, migration tool, validation approach, auth mechanism, search tool, AI tools, and naming conventions. All section checks below are conditional on what is defined here.
2. Read `.claude/plans/$ARGUMENTS.md` — the approved plan to check against

If no argument is given, list available plans:
```bash
ls .claude/plans/
```
Then ask the user which plan to check.

If the plan status is not `APPROVED`, warn:
> "⚠️ This plan has status **<status>** — adherence check will proceed but the plan has not been formally approved."

## Step 2: Identify code in scope

Determine what code to evaluate:
- If a branch/PR exists: files changed vs base branch (`git diff main...HEAD --name-only`)
- If not in git: ask the user to point to relevant files or packages
- Always include test files — test coverage is part of adherence

## Step 3: Score each plan section

Evaluate each section of the plan against the code. Assign a score per section:

| Score | Meaning |
|---|---|
| ✅ Full | Code fully matches the plan section |
| 🟡 Partial | Mostly implemented, minor gaps |
| 🔴 Missing | Plan section not implemented at all |
| ⚠️ Deviated | Implemented differently from the plan |
| N/A | Not applicable to this iteration |

### Sections to check

**Domain Model** — Does every planned entity, field, and relationship exist?
- Compare plan Section 2 against entity classes per STACK.md ORM
- Check ORM mappings match planned fetch strategies
- Check database migration files exist per STACK.md migration tool

**Repository Layer** — Do planned repositories and custom queries exist?
- Plan Section 3 vs repository interfaces per STACK.md ORM/repository pattern
- Check custom query methods match planned query patterns
- Check search repository changes if planned — per STACK.md search tool

**Service Layer** — Do planned service methods exist with correct transaction rules?
- Plan Section 4 vs service classes per STACK.md conventions
- Verify transaction placement matches plan — per STACK.md transaction conventions
- Verify business logic summary is reflected in method names/structure

**REST API Contract** — Do endpoints match the plan exactly?
- Plan Section 5 vs controller classes per STACK.md API style
- Method, path, request body, response body, HTTP status codes
- Validation annotations per STACK.md validation approach

**AI / Agentic Integration** — If planned and STACK.md lists an AI tool:
- Plan Section 6 — model, API type, prompt strategy, error handling
- Retry and timeout logic present?
- AI client call outside transaction boundary?

**Search Integration** — If planned and STACK.md lists a search tool:
- Plan Section 7 — index changes, query patterns per STACK.md search tool

**Security** — Are planned auth/authz rules implemented?
- Plan Section 8 vs security config per STACK.md auth mechanism

**Test Coverage** — Does each acceptance criterion have a test?
- Plan Section 9 — map each criterion to a test method
- Missing tests = adherence gap

## Step 4: Produce the adherence report

Output as markdown (user can save to `.claude/plans/<name>-adherence.md`):

```markdown
# Plan Adherence Report: <feature name>
**Plan:** .claude/plans/<name>.md
**Checked:** <date>
**Overall Score:** <X>/<total> sections fully adherent

## Section Scores
| Section | Score | Notes |
|---|---|---|
| Domain Model | ✅/🟡/🔴/⚠️ | ... |
| Repository Layer | ... | ... |
| Service Layer | ... | ... |
| REST API Contract | ... | ... |
| OpenAI/ADK | ... | ... |
| Solr | ... | ... |
| Security | ... | ... |
| Test Coverage | ... | ... |

## Adherence Score: XX%
> Calculated as: (Full×1 + Partial×0.5) / applicable sections × 100

## Verdict
🟢 PASS (≥80%) | 🟡 CONDITIONAL (60–79%) | 🔴 FAIL (<60%)

---

## Deviations (⚠️)
List each case where code differs from the plan:
- **[Section]** `ClassName.java` — Plan specified X, code does Y. Reason unknown — flag for architect review.

## Gaps (🔴)
List each unimplemented plan item:
- **[Section]** — <what is missing>

## Partial implementations (🟡)
- **[Section]** `ClassName.java` — <what's done, what's missing>

## Recommendations
1. <Specific action to reach full adherence>
```

## Step 5: Offer next steps

After the report, ask:
> "Should I fix the gaps and deviations now? I'll prioritize 🔴 Missing and ⚠️ Deviations first."

If yes, address items in order. For each fix, re-run the relevant section check after completing it.

## Scoring guidance

- A score ≥ 80% → safe to proceed to PR
- A score 60–79% → PR allowed with acknowledged gaps documented
- A score < 60% → implementation is not ready; return to coding phase
