---
allowed-tools: Bash(git diff*), Bash(git log*), Bash(git show*), Bash(git merge-base*)
argument-hint: ["--top N", "--fix", "--scope", "--base"]
context: ["fork"]
model: "opus"
description: "Review PR changes for code quality, DRY violations, antipatterns, and improvement opportunities"
---

# PR Code Review

Perform a senior engineer-level code review focused on making changes easier and cleaner for the next developer.

## Arguments

Parse from input: $ARGUMENTS

| Argument  | Default | Description                                 |
|-----------|---------|---------------------------------------------|
| `--top N` | 5       | Number of issues to surface                 |
| `--fix`   | off     | Apply recommended fixes after review        |
| `--scope` | pr      | What to review: `pr`, `staged`, or `branch` |
| `--base`  | main    | Base branch for diff comparison             |

## Execution

### Phase 1: Scope Discovery

Determine what changed:

```bash
# For PR/branch scope
git diff -U10 --name-status $(git merge-base HEAD <base>)..HEAD

# For staged scope
git diff -U10 --name-status --cached
```
- important! remember that you ALREADY ARE in the project directory, no need to `cd` into it!

Categorize: new files, modified, renamed/moved.

### Phase 2: Deep Analysis

Think carefully through each category. Take your time—thoroughness matters more than speed.

**DRY Violations**
- Duplicated logic across changed files
- Copy-paste patterns that should be abstracted
- Repeated error handling, validation, or transformations

**Dead Code**
- Unused functions, variables, imports introduced by this PR
- Orphaned code from incomplete refactoring
- Commented-out code blocks

**Antipatterns**
- God objects/functions doing too much
- Inappropriate coupling between modules
- Single responsibility violations
- Magic numbers/strings without constants

**Bad Abstractions**
- Premature or over-engineering
- Leaky abstractions exposing implementation details
- Wrong abstraction level for the problem domain
- Inheritance where composition fits better

**Size & Complexity**
- Functions exceeding ~50 lines
- Files exceeding ~400 lines
- Deeply nested conditionals (>3 levels)
- Parameter lists with >5 params

### Phase 3: Prioritization

Rank findings by:

1. **Impact** — How much does this hurt maintainability?
2. **Effort** — How hard is it to fix?
3. **Scope** — Isolated or widespread?
4. **Risk** — Could the fix introduce regressions?

Keep only the top N issues worth addressing.

### Phase 4: Report

## Output Format

```
## PR Code Review — Top {N} Improvements

### 1. [Category] Brief Title

**Location**: `path/to/file.ts:42-58`
**Impact**: High | Medium | Low
**Effort**: Quick | Moderate | Significant

**Problem**: What's wrong and why it matters for maintainability.

**Recommendation**:
Concrete fix with code example if helpful.

---

### 2. ...

---

## Summary

- Issues surfaced: X of Y total
- Quick wins (< 5 min): N
- Larger refactors: N
```

## If --fix is set

After presenting the report, ask for confirmation, then apply fixes one at a time. Use TodoWrite to track progress if multiple fixes are needed.