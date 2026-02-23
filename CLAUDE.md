# CLAUDE.md

Demo repo for GitHub Actions `branches-ignore` filtering patterns.

## Structure

- `.github/workflows/main.yml` — single workflow (`CI Flow`) triggered on `pull_request`
- `.claude/commands/docs_sync.md` — custom command for PR-driven doc updates
- `justfile` — dev task runner (requires [just](https://github.com/casey/just))

## Development

| Command     | Description              |
|-------------|--------------------------|
| `just lint` | Run ruff linter (`uv run ruff check .`) |

## Branch Filtering

The workflow uses `branches-ignore` to skip PRs targeting:
- `mona/octocat` (exact match)
- `releases/**-alpha` (glob pattern)

Ref: [GH docs — excluding branches](https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#example-excluding-branches)
