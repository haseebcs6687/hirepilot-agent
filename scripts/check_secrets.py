#!/usr/bin/env python3
"""Pre-commit security checker for HirePilot.

Scans staged files to ensure no sensitive files (e.g. private/, .env, credentials)
or secret tokens (API keys, private keys) are committed to the repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# Paths or patterns that must never be staged
FORBIDDEN_PATH_PATTERNS = [
    r"^private/",
    r"^\.env($|\..*)",
    r".*\.db($|\..*)",
    r".*\.sqlite.*",
    r".*credentials.*\.json$",
    r".*token.*\.json$",
    r".*\.pem$",
    r".*\.key$",
]

# Regex patterns for API keys and tokens in added/modified content
SUSPICIOUS_CONTENT_PATTERNS = [
    (r"AIza[0-9A-Za-z-_]{35}", "Google / Gemini API Key"),
    (r"gsk_[a-zA-Z0-9]{40,}", "Groq API Key"),
    (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
    (r"sk-[a-zA-Z0-9]{40,}", "Generic Secret Key / OpenAI Key"),
    (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "Private Key Header"),
    (
        r"(?i)(api[_-]?key|secret[_-]?key|auth[_-]?token|access[_-]?token)\s*[:=]\s*['\"][0-9a-zA-Z\-_]{16,}['\"]",
        "Hardcoded Secret Assignment",
    ),
]

# Allow-list files where placeholder keys are expected
ALLOWED_FILES = {
    ".env.example",
    "private.example",
    "scripts/check_secrets.py",
}


def get_staged_files() -> list[str]:
    """Return a list of staged file paths."""
    res = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in res.stdout.splitlines() if line.strip()]


def check_paths(staged_files: list[str]) -> list[str]:
    """Check if any staged file paths match forbidden paths."""
    violations = []
    for file_path in staged_files:
        norm_path = file_path.replace("\\", "/")
        if any(norm_path.startswith(allowed) or norm_path == allowed for allowed in ALLOWED_FILES):
            continue
        for pattern in FORBIDDEN_PATH_PATTERNS:
            if re.search(pattern, norm_path, re.IGNORECASE):
                violations.append(
                    f"[FORBIDDEN FILE] {file_path} matches forbidden pattern '{pattern}'"
                )
    return violations


def check_staged_content(staged_files: list[str]) -> list[str]:
    """Check staged diffs for secret key patterns."""
    violations = []
    for file_path in staged_files:
        norm_path = file_path.replace("\\", "/")
        # Skip checking allowed example / documentation files
        if any(norm_path.startswith(allowed) or norm_path == allowed for allowed in ALLOWED_FILES):
            continue

        res = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", file_path],
            capture_output=True,
            text=True,
            check=True,
        )
        for line in res.stdout.splitlines():
            # Only examine added lines (starting with + and not +++)
            if line.startswith("+") and not line.startswith("+++"):
                line_content = line[1:].strip()
                for pattern, desc in SUSPICIOUS_CONTENT_PATTERNS:
                    if re.search(pattern, line_content):
                        violations.append(
                            f"[SECRET DETECTED] {file_path}: Potential {desc} detected in staged line."
                        )
                        break
    return violations


def main() -> int:
    print("[HirePilot Pre-Commit Security Check] Scanning staged files...")
    try:
        staged = get_staged_files()
    except subprocess.CalledProcessError as e:
        print(f"Error checking git staged files: {e}", file=sys.stderr)
        return 1

    if not staged:
        print("No staged files found. Check passed.")
        return 0

    path_violations = check_paths(staged)
    content_violations = check_staged_content(staged)

    all_violations = path_violations + content_violations
    if all_violations:
        print("\n" + "=" * 60, file=sys.stderr)
        print("SECURITY CHECK FAILED! Secrets or forbidden files detected:", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        for v in all_violations:
            print(f"  - {v}", file=sys.stderr)
        print("\nPlease remove secrets or unstage sensitive files before committing.", file=sys.stderr)
        return 1

    print(f"Security check passed. {len(staged)} staged file(s) verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
