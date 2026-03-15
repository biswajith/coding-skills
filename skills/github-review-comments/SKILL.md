---
name: github-review-comments
description: Fetches GitHub PR review comments using the gh CLI, groups them by theme, and produces a prioritized action plan to address each comment. Use when addressing PR feedback, responding to code review, or when the user mentions review comments, PR comments, or "what do I need to fix".
disable-model-invocation: true
allowed-tools: Bash(gh *)
---

# GitHub Review Comments → Action Plan

Fetch all review comments on a PR, analyze them, and produce a prioritized action plan.

## Step 1: Get the PR number

Argument: `$ARGUMENTS` — can be a PR number (e.g. `42`) or a full PR URL.

If no argument provided, run:
```bash
gh pr list --state open
```
Then ask the user which PR to address.

## Step 2: Fetch review data

Run all three commands to get full context:

```bash
gh pr view $ARGUMENTS --json title,body,author,baseRefName,headRefName,state
gh pr reviews $ARGUMENTS --json author,state,body,submittedAt
gh api repos/{owner}/{repo}/pulls/$ARGUMENTS/comments --paginate \
  --jq '.[] | {id:.id, path:.path, line:.line, body:.body, author:.user.login, resolved:.position}'
```

For the repo owner/repo, detect from:
```bash
gh repo view --json nameWithOwner --jq '.nameWithOwner'
```

## Step 3: Categorize comments

Group comments into these buckets (a comment can appear in multiple):

| Category | Examples |
|---|---|
| **Bug / Correctness** | logic errors, null safety, wrong behavior |
| **Plan Deviation** | code doesn't match approved design |
| **Security** | injection, hardcoded secrets, auth gaps |
| **Performance** | N+1, missing indexes, unbounded queries |
| **Test Coverage** | missing tests, weak assertions |
| **Code Quality** | naming, complexity, dead code |
| **Style / Convention** | formatting, project conventions from `STACK.md` |

## Step 4: Produce the action plan

Output a markdown document the user can save as `.claude/plans/pr-<number>-action-plan.md`:

```markdown
# PR #<number> Review Action Plan
**PR:** <title>
**Branch:** <headRef> → <baseRef>
**Generated:** <date>

## Summary
<N> comments from <M> reviewers. <X> require code changes.

## Action Items

### 🔴 Must Fix (Bugs, Security, Plan Deviations)
- [ ] **[Reviewer]** `path/to/File.java:line` — <comment summary>
  - Action: <specific thing to do>

### 🟡 Should Fix (Performance, Test Coverage, Quality)
- [ ] **[Reviewer]** `path/to/File.java:line` — <comment summary>
  - Action: <specific thing to do>

### 🟢 Consider (Style, Convention)
- [ ] **[Reviewer]** `path/to/File.java:line` — <comment summary>
  - Action: <specific thing to do>

## Grouped by file
<List files with their action items>

## Reviewer responses needed
<Comments that are questions requiring clarification before coding>
```

## Step 5: Offer to execute

After presenting the plan, ask:
> "Should I start implementing these fixes? If yes, I'll work through the 🔴 Critical items first using the TDD workflow."

If yes, address items in priority order: 🔴 → 🟡 → 🟢. For each fix:
1. Read the file at the flagged line
2. Apply the fix
3. Update the checklist item to ✅

## Notes

- Resolved/outdated comments (where `position` is null) are noted but deprioritized
- If `.claude/STACK.md` exists, read it to judge style/convention comments accurately against project conventions
- If a comment references the feature plan, cross-check `.claude/plans/` for the relevant plan doc
- Related skills: `/architect-plan` to produce a plan, `/tdd-workflow` to implement, `/code-review` to validate, `/plan-adherence` to score compliance
