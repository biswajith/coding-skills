---
name: tdd-workflow
description: Drives a strict Red-Green-Refactor TDD cycle driven by the project's STACK.md and an approved plan document. Use when implementing a feature, writing tests first, or when the user says "implement", "build", or "write tests for" a feature. Requires an approved plan document.
disable-model-invocation: true
---

# TDD Workflow

You are a disciplined engineer executing an approved architectural plan using strict TDD. You write the test first. You do not write implementation code until a failing test exists.

## Step 1: Load context

Read both files before writing any code:
1. `.claude/STACK.md` — defines: language version, frameworks, test frameworks, naming conventions, package structure, integration test approach
2. `.claude/plans/$ARGUMENTS.md` — the approved feature plan (acceptance criteria become test cases)

If either file is missing:
- No `STACK.md` → tell user to create it from the template in [STACK-TEMPLATE.md](STACK-TEMPLATE.md)
- No plan file → tell user to run `/architect-plan` first and get it approved

If no plan name was passed as an argument, ask the user which plan to implement.

All test framework choices, naming conventions, and integration test tooling must come from STACK.md — do not assume specific libraries unless listed there.

## Step 2: Map acceptance criteria to test cases

From the plan's **Section 9 (Acceptance Criteria)**, produce a test case table:

| # | Acceptance Criterion | Test class | Test method name |
|---|---|---|---|
| 1 | ... | ...ServiceTest | <per STACK.md naming convention> |

Use the naming convention from `STACK.md`. Present this table and ask for confirmation before writing any code.

## Step 3: Red-Green-Refactor cycle

For each test case, strictly follow this loop:

### RED
- Write the test only — no implementation
- Use the unit test framework specified in STACK.md
- Mock dependencies with the mocking library specified in STACK.md
- For integration tests, use the integration test approach specified in STACK.md
- Confirm the test compiles but fails before proceeding

### GREEN
- Write the **minimum** implementation to make the test pass
- No gold-plating — only what the test demands
- Follow package structure and patterns from STACK.md

### REFACTOR
- Clean up duplication, improve naming, apply patterns
- Tests must still pass after refactor
- Apply language-version idioms appropriate to the Java version in STACK.md

Move to the next test case only after the current one is green and refactored.

## Layer-specific guidance

All guidance below is conditional on what STACK.md specifies.

### Entity / Repository tests
- Test repository methods with the slice test annotation appropriate to the ORM in STACK.md
- Verify fetch strategies don't produce N+1 queries
- For search repositories: use the embedded or mock approach appropriate to the search tool in STACK.md

### Service tests
- Pure unit tests — no application context unless integration test
- Verify transaction boundary behavior where critical
- Any external API call (AI, HTTP) must not be inside a transaction — if the plan implies this, flag it

### Controller / API tests
- Use the lightest test slice that covers the layer — per STACK.md API style
- Test request validation (expect 4xx for invalid input)
- Test error responses from the error handler defined in STACK.md conventions

### AI / Agentic tests
- Mock the AI client at the service boundary — per STACK.md AI SDK
- Test: success path, rate-limit exception, timeout, malformed response
- For agentic frameworks: mock tool calls, verify tool invocation sequences

## Language-version idioms (apply during REFACTOR)

Read the Java version from STACK.md and apply appropriate idioms:
- **Java 16+**: `record` types for immutable DTOs, `instanceof` pattern matching
- **Java 17+**: sealed interfaces for discriminated results
- **Java 21+**: switch pattern matching, virtual threads for I/O-bound work (if executor configured)
- **Earlier versions**: follow conventions from STACK.md without assuming newer features

## Progress tracking

Maintain this checklist as you work:

```
TDD Progress — <feature name>
- [ ] Test case 1: <name>
- [ ] Test case 2: <name>
...
```

Mark each item complete (✅) after Green + Refactor.
