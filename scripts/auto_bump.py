# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""
Pre-commit hook: keep pyproject.toml version > origin/main and uv.lock in sync.

Behaviour
---------
- If `pyproject.version <= origin/main:pyproject.version`: bump patch, run `uv lock`,
  stage both files. First divergent commit on a branch carries the bump.
- Else if pyproject.toml is staged (deps changed): re-run `uv lock`, stage uv.lock.
- Else: no-op.

Replaces the in-CI bumper (#224 follow-up). All version decisions happen
client-side, sequentially, before push — so CI becomes a read-only validator.

Skipped quietly when:
- not a git repo / pyproject.toml absent
- origin/main unreachable (fresh clone, detached state, etc.) — CI will still validate
"""

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


def write_version(new: str) -> None:
    text = PYPROJECT.read_text(encoding="utf-8")
    new_text, n = VERSION_LINE.subn(rf'\1"{new}"', text, count=1)
    if n != 1:
        raise RuntimeError("Could not find a `version = \"X.Y.Z\"` line to rewrite")
    PYPROJECT.write_text(new_text, encoding="utf-8")


def run_uv_lock() -> None:
    subprocess.run(["uv", "lock", "--quiet"], check=True)


def stage(*paths: str) -> None:
    subprocess.run(["git", "add", "--", *paths], check=True)


def main() -> int:
    if not PYPROJECT.exists():
        return 0

    head = read_version(PYPROJECT.read_text(encoding="utf-8"))
    ref = base_ref()
    base = fetch_base_version(ref)

    if base is None:
        print(
            f"auto_bump: {ref} unreachable — skipping (CI will validate)",
            file=sys.stderr,
        )
        return 0

    pyproject_dirty = is_staged("pyproject.toml")

    if parse(head) <= parse(base):
        new = bump_patch(head)
        write_version(new)
        print(f"auto_bump: {head} -> {new} (was <= base {base})", file=sys.stderr)
        pyproject_dirty = True

    if pyproject_dirty:
        run_uv_lock()
        stage("pyproject.toml", "uv.lock")

    return 0


if __name__ == "__main__":
    sys.exit(main())
