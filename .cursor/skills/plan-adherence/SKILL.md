---
name: plan-adherence
description: Measures how faithfully the current codebase or changed files match an approved feature plan. Produces a scored adherence report with deviations, gaps, and a pass/fail verdict. Use when validating implementation against a plan, before a PR, or when the user asks "does the code match the plan", "plan compliance", or "adherence check".
disable-model-invocation: true
---

# Plan Adherence Check

Measure how faithfully the code matches an approved plan document. Produces a scored report and explicit list of deviations.

## Step 1: Load context

1. Read `.claude/STACK.md` for project conventions
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
- Compare plan Section 2 against `@Entity` classes
- Check Hibernate mappings match planned fetch strategies
- Check Liquibase/Flyway migrations cover all schema changes

**Repository Layer** — Do planned repositories and custom queries exist?
- Plan Section 3 vs `@Repository` interfaces
- Check custom `@Query` methods match planned query patterns
- Check Solr repository changes if planned

**Service Layer** — Do planned service methods exist with correct transaction rules?
- Plan Section 4 vs `@Service` classes
- Verify `@Transactional` placement matches plan
- Verify business logic summary is reflected in method names/structure

**REST API Contract** — Do endpoints match the plan exactly?
- Plan Section 5 vs `@RestController` classes
- Method, path, request body, response body, HTTP status codes
- Validation annotations (`@Valid`, `@NotNull`, etc.)

**OpenAI / ADK Integration** — If planned, is it implemented correctly?
- Plan Section 6 — model, API type, prompt strategy, error handling
- Retry and timeout logic present?
- OpenAI call outside `@Transactional`?

**Solr Integration** — If planned, is it implemented correctly?
- Plan Section 7 — index changes, query patterns

**Security** — Are planned auth/authz rules implemented?
- Plan Section 8 vs Spring Security config

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
