#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Fail CI if forbidden raw GitHub URL is introduced in new diff lines."""

import argparse
import fnmatch
import re
import subprocess
import sys


FORBIDDEN_EXTERNAL_URL_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com"
)
RECOMMENDED_INTERNAL_URL = "https://azcliprod.blob.core.windows.net/cli"

# Paths matching these glob patterns are excluded from the check.
# Exclusions cover documentation, test source files, test recordings, and test data.
EXCLUDED_PATH_PATTERNS = [
    "*.md",
    "*.rst",
    "doc/*",
    "docs/*",
    "*/doc/*",
    "*/docs/*",
    "scripts/*",
    "*/tests/recordings/*",
    "*/tests/*.py",
    "*/tests/*.json",
    "*/tests/*.yaml",
    "*/tests/*.yml",
    "*/tests/*/recordings/*",
    "*/tests/*/test_*.py",
    "*/tests/*/*.json",
    "*/tests/*/*.yaml",
    "*/tests/*/*.yml",
]


def _is_excluded(file_path: str) -> bool:
    """Return True if *file_path* matches one of the exclusion glob patterns."""
    for pattern in EXCLUDED_PATH_PATTERNS:
        if fnmatch.fnmatch(file_path, pattern):
            return True
    return False


def _run_diff(src: str, tgt: str, cached: bool = False) -> str:
    cmd = ["git", "diff", "--unified=0", "--no-color"]
    if cached:
        cmd.append("--cached")
    else:
        cmd.append(f"{tgt}...{src}")

    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "git diff failed")
    return proc.stdout


def _find_violations(diff_text: str):
    violations = []
    current_file = ""

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            continue

        if not line.startswith("+") or line.startswith("+++"):
            continue

        added_line = line[1:]
        if FORBIDDEN_EXTERNAL_URL_PATTERN.search(added_line) and not _is_excluded(current_file):
            violations.append((current_file or "<unknown>", added_line.strip()))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check diff for forbidden raw github URL usage.")
    parser.add_argument("--src", default="HEAD", help="Source ref/commit for git diff.")
    parser.add_argument("--tgt", default="HEAD~1", help="Target ref/commit for git diff.")
    parser.add_argument("--cached", action="store_true", help="Check staged changes in git index.")
    args = parser.parse_args()

    try:
        diff_text = _run_diff(src=args.src, tgt=args.tgt, cached=args.cached)
    except Exception as ex:  # pylint: disable=broad-except
        if args.cached:
            print(f"Unable to evaluate staged diff: {ex}", file=sys.stderr)
        else:
            print(f"Unable to evaluate diff between '{args.tgt}' and '{args.src}': {ex}", file=sys.stderr)
        return 1

    violations = _find_violations(diff_text)
    if not violations:
        print("No forbidden external github URL found in added lines.")
        return 0

    print("Found forbidden external github URL in this change:", file=sys.stderr)
    for file_path, content in violations:
        print(f"  - {file_path}: {content}", file=sys.stderr)

    print(
        f"Use '{RECOMMENDED_INTERNAL_URL}' instead of raw GitHub URLs to limit external system access.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

