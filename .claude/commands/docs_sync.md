---
allowed-tools: Bash(git diff*), Bash(git log*), Bash(git show*), Bash(git merge-base*)
argument-hint: ["--fix", "--base"]
context: ["fork"]
model: "opus"
description: "Analyze PR changes and suggest documentation updates for CLAUDE.md"
---

# Documentation Sync

Analyze PR changes to identify documentation updates needed for CLAUDE.md and its referenced files.

## Arguments

Parse from input: $ARGUMENTS

| Argument | Default | Description                             |
|----------|---------|-----------------------------------------|
| `--fix`  | off     | Apply documentation updates immediately |
| `--base` | main    | Base branch for diff comparison         |

## Execution

### Phase 1: Scope Discovery

Get changed files and their status:

```bash
git diff --name-status $(git merge-base HEAD <base>)..HEAD
```
- important! remember that you ALREADY ARE in the project directory, no need to `cd` into it!

Categorize:
- New files (added)
- Modified files
- Renamed/moved files
- Deleted files

### Phase 2: Context Loading

Read documentation files:
- `CLAUDE.md`
- `docs/internal/FRAMEWORK.md`
- `docs/internal/API.md`
- `docs/internal/FRONT.md`
- `docs/internal/QA.md`
- `docs/internal/SECURITY.md`
- `docs/internal/style-guide.md`

Map existing documentation structure to understand what's already covered.

### Phase 3: Deep Analysis

For each significant change, determine if documentation needs updating.

**New Directories/Modules**
- Should be added to Architecture or Key Files sections?
- New packages/namespaces worth documenting?

**New Patterns/Conventions**
- Code patterns introduced that others should follow?
- New import patterns, naming conventions?
- Should be added to "Important Patterns" section?

**Configuration Changes**
- New config options, environment variables?
- New secrets or Doppler keys?
- Should be in "Configuration System" or "Environment & Secrets"?

**Testing Infrastructure**
- New test base classes, utilities, factories?
- New test patterns or fixtures?
- Should be in "Testing Patterns" section?

**New Integrations**
- New external APIs, services, libraries?
- Should be added to integration sections?

**CLI Commands**
- New just commands or scripts?
- Should be in "Development Commands"?

**Architecture Changes**
- New services, layers, or architectural patterns?
- Should be in "Architecture" section?

**Breaking Changes**
- Changes that require updating existing docs?
- Deprecations or removals?

### Phase 4: Report Generation

For each finding, provide:

```
## Documentation Sync — Suggested Updates

### 1. [Category] Brief Description

**File to Update**: `CLAUDE.md` or `docs/internal/X.md`
**Section**: Specific section name
**Priority**: High | Medium | Low

**Change Detected**:
Description of what changed in the codebase.

**Suggested Documentation**:
```
Proposed content to add/update in the documentation file.
Include proper formatting and markdown.
```

**Reasoning**:
Why this documentation helps future developers.

---

### 2. ...

---

## Summary

- Updates needed: X
- High priority: N
- Medium priority: N
- Low priority: N
```

### Phase 5: Fix Mode (if --fix is set)

If `--fix` is set:

1. Present the full report
2. Ask for confirmation: "Should I apply these X documentation updates?"
3. If approved, use TodoWrite to track updates:
   - Each documentation file edit as a separate task
   - Mark in_progress before editing
   - Mark completed after each edit
4. Apply updates one file at a time using Edit tool
5. Verify each edit was successful

## Guidelines

**Quality Checks**:
- Don't document internal implementation details that change frequently
- Focus on patterns, conventions, and architecture
- Keep documentation concise and scannable
- Use tables, bullet points, code examples
- Reference files with relative paths
- Follow existing documentation style

> **IMPORTANT:** remember that we must keep the initial context minimal (!)
> Your goal is to prevent the context bloating; our developers already know good
> practices, patterns, etc. We only should add things they don't know, but absolutely SHOULD 

1. DO NOT add the information that's not EXTREMELY IMPORTANT and RELEVANT to the given documentation
ASK YOURSELF? are you sure the next developer needs to know this when working on the new feature, bug fix, etc?
If not, don't add it.
2. If some reference could be removed because e.g. file was removed in refactoring, removing it HAS HIGHEST PRIORITY!
- the same goes to updating the information that's no longer relevant!

**What NOT to document**:
- Trivial changes (typos, formatting)
- Temporary debugging code
- Changes to test data/fixtures (unless pattern-worthy)
- Private helper functions
- One-off bug fixes

**What TO document**:
- New important, likely to be reused abstractions or patterns
- New public APIs or interfaces
- Architecture changes
- New development workflows
- Breaking changes
- New dependencies or integrations
- If something was deleted, delete the reference to it as well!
