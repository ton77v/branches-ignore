# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Bump pyproject.toml version above the base branch + keep uv.lock in sync.

Used by the in-CI bumper (.github/workflows/version-bump.yml) to produce
a single atomic commit per PR (vs. apowis's 3-push flow). Also runnable
locally for sanity checks.

Behaviour
---------
- If `pyproject.version <= base:pyproject.version`: bump patch + re-lock.
- Else if uv.lock is out of sync (manual bump forgot `uv lock`): re-lock.
- Else: no-op.

Flags
-----
--base <ref>   Base ref like "origin/main". Auto-detected via symbolic-ref
               or origin/main|master fallback when omitted.
--no-stage     Skip `git add` (caller does its own commit; CI uses this).

Skipped quietly when:
- pyproject.toml absent
- base ref unreachable (fresh clone, etc.)
"""

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

PYPROJECT = Path("pyproject.toml")
VERSION_LINE = re.compile(r'(?m)^(version\s*=\s*)"[^"]+"')


def base_ref() -> str:
    """Resolve the default branch (main / master / etc.) without hardcoding."""
    try:
        out = subprocess.check_output(
            ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        # e.g. "refs/remotes/origin/main" -> "origin/main"
        return out.replace("refs/remotes/", "", 1)
    except subprocess.CalledProcessError:
        # Fresh clone with no symbolic-ref set; fall back to common names.
        for candidate in ("origin/main", "origin/master"):
            try:
                subprocess.check_output(
                    ["git", "rev-parse", "--verify", candidate],
                    stderr=subprocess.DEVNULL,
                )
                return candidate
            except subprocess.CalledProcessError:
                continue
        return "origin/main"  # best-effort default; fetch will fail loudly


def parse(v: str) -> tuple[int, ...]:
    return tuple(int(p) for p in v.split("."))


def read_version(content: str) -> str:
    return tomllib.loads(content)["project"]["version"]


def bump_patch(v: str) -> str:
    parts = v.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    return ".".join(parts)


def fetch_base_version(ref: str) -> str | None:
    try:
        # ref like "origin/main" -> fetch "main"
        branch = ref.split("/", 1)[1] if "/" in ref else ref
        subprocess.run(
            ["git", "fetch", "origin", branch, "--quiet"],
            check=False,
            capture_output=True,
        )
        content = subprocess.check_output(
            ["git", "show", f"{ref}:pyproject.toml"],
            text=True,
            stderr=subprocess.DEVNULL,
        )
        return read_version(content)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def is_staged(path: str) -> bool:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--", path],
        capture_output=True,
        text=True,
        check=True,
    )
    return bool(result.stdout.strip())


def lockfile_in_sync() -> bool:
    """`uv lock --check` — exit 0 if lockfile matches pyproject.toml."""
    result = subprocess.run(["uv", "lock", "--check"], capture_output=True)
    return result.returncode == 0


def write_version(new: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text, n = VERSION_LINE.subn(rf'\1"{new}"', text, count=1)
    if n != 1:
        raise RuntimeError('Could not find a `version = "X.Y.Z"` line to rewrite')
    PYPROJECT.write_text(new_text, encoding="utf-8")


def run_uv_lock() -> None:
    subprocess.run(["uv", "lock", "--quiet"], check=True)


def stage(*paths: str) -> None:
    subprocess.run(["git", "add", "--", *paths], check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=None, help="Base ref (e.g. origin/main); auto-detect if omitted")
    parser.add_argument("--no-stage", action="store_true", help="Skip git add (caller commits separately)")
    args = parser.parse_args()

    if not PYPROJECT.exists():
        return 0

    head = read_version(PYPROJECT.read_text(encoding="utf-8"))
    ref = args.base or base_ref()
    base = fetch_base_version(ref)

    if base is None:
        print(f"auto_bump: {ref} unreachable — skipping", file=sys.stderr)
        return 0

    needs_lock = is_staged("pyproject.toml")

    if parse(head) <= parse(base):
        new = bump_patch(head)
        write_version(new)
        print(f"auto_bump: {head} -> {new} (was <= base {base})", file=sys.stderr)
        needs_lock = True
    elif not needs_lock and not lockfile_in_sync():
        # Catches the "manual bump forgot uv lock" case in CI's clean checkout.
        print("auto_bump: lockfile out of sync with pyproject.toml — re-locking", file=sys.stderr)
        needs_lock = True

    if needs_lock:
        run_uv_lock()
        if not args.no_stage:
            stage("pyproject.toml", "uv.lock")

    return 0


if __name__ == "__main__":
    sys.exit(main())
