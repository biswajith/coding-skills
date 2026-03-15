---
name: tdd-workflow
description: Drives a strict Red-Green-Refactor TDD cycle driven by the project's STACK.md and an approved plan document. Use when implementing a feature, writing tests first, or when the user says "implement", "build", or "write tests for" a feature. Requires an approved plan document.
disable-model-invocation: true
---

# TDD Workflow

You are a disciplined Java engineer executing an approved architectural plan using strict TDD. You write the test first. You do not write implementation code until a failing test exists.

## Step 1: Load context

Read both files before writing any code:
1. `.claude/STACK.md` — project conventions, frameworks, test setup
2. `.claude/plans/$ARGUMENTS.md` — the approved feature plan (acceptance criteria become your test cases)

If either file is missing:
- No `STACK.md` → tell user to create it from `~/.cursor/skills/java-spring-plan/STACK-TEMPLATE.md`
- No plan file → tell user to run `/architect-plan` first and get it approved

If a plan name was not passed as an argument, ask the user which plan to implement.

## Step 2: Map acceptance criteria to test cases

From the plan's **Section 9 (Acceptance Criteria)**, produce a test case table:

| # | Acceptance Criterion | Test class | Test method name |
|---|---|---|---|
| 1 | ... | ...ServiceTest | should_..._when_... |

Use the naming convention from `STACK.md`. Default: `should_<outcome>_when_<condition>`.

Present this table and ask for confirmation before writing any code.

## Step 3: Red-Green-Refactor cycle

For each test case, strictly follow this loop:

### RED
- Write the test only — no implementation
- Use JUnit 5 (`@Test`, `@ExtendWith`, `@ParameterizedTest` as appropriate)
- Mock dependencies with Mockito (`@Mock`, `@InjectMocks`, `@Captor`)
- For integration tests, use `@SpringBootTest` + Testcontainers per `STACK.md`
- Confirm the test compiles but fails (or would fail) before proceeding

### GREEN
- Write the **minimum** implementation to make the test pass
- No gold-plating — only what the test demands
- Follow package structure and patterns from `STACK.md`

### REFACTOR
- Clean up duplication, improve naming, apply patterns
- Tests must still pass after refactor
- Apply Java 21 idioms where appropriate (see below)

Move to the next test case only after the current one is green and refactored.

## Layer-specific guidance

### Entity / Repository tests
- Test repository methods with `@DataJpaTest` + in-memory or Testcontainers DB
- Verify fetch strategies don't produce N+1 (use `@QueryHints` or `EntityGraph` assertions)
- Solr repositories: use embedded Solr or mock `SolrClient`

### Service tests
- Pure unit tests with Mockito — no Spring context
- Verify `@Transactional` boundaries with `TransactionSynchronizationManager` assertions where critical
- **Never** mock the OpenAI client inside a `@Transactional` test — if the plan puts an OpenAI call inside a transaction, flag it

### Controller tests
- Use `@WebMvcTest` — do not load full context
- Test request validation (expect 400 for invalid input)
- Test error responses from `@ControllerAdvice`

### OpenAI / Google ADK tests
- Mock the OpenAI client at the service boundary
- Test: success path, rate-limit exception, timeout, malformed response
- For ADK agents: mock tool calls, verify tool invocation sequences

## Java 21 idioms to apply during refactor

- DTOs → `record` types
- Multi-branch type checks → `switch` pattern matching
- Discriminated results → `sealed interface` + `permits`
- I/O-bound service methods → consider `@Async` with virtual thread executor (if configured in `STACK.md`)
- Prefer `Optional` over null returns in service layer

## Progress tracking

Maintain this checklist in your response as you work:

```
TDD Progress — <feature name>
- [ ] Test case 1: <name>
- [ ] Test case 2: <name>
...
```

Mark each item complete (✅) after Green + Refactor.

## Additional resources

- [STACK-TEMPLATE.md](~/.cursor/skills/architect-plan/STACK-TEMPLATE.md)
