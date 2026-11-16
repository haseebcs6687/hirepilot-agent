#!/usr/bin/env python3
"""Setup Git pre-commit hooks for HirePilot."""

import os
import stat
from pathlib import Path

HOOK_CONTENT = """#!/bin/sh
# HirePilot pre-commit hook to prevent secret leaks
python scripts/check_secrets.py
if [ $? -ne 0 ]; then
    echo "Aborting commit due to security check failure."
    exit 1
fi
"""


def install_hooks() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    hooks_dir = repo_root / ".git" / "hooks"

    if not hooks_dir.exists():
        print(f"Git hooks directory not found at {hooks_dir}. Is this a git repository?")
        return

    pre_commit_path = hooks_dir / "pre-commit"
    with open(pre_commit_path, "w", encoding="utf-8") as f:
        f.write(HOOK_CONTENT)

    # Make executable on Unix-like systems
    st = os.stat(pre_commit_path)
    os.chmod(pre_commit_path, st.st_mode | stat.S_IEXEC)

    print(f"Pre-commit hook successfully installed at: {pre_commit_path}")


if __name__ == "__main__":
    install_hooks()
