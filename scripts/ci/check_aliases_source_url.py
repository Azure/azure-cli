#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Fail CI if forbidden raw GitHub aliases URL is introduced in new diff lines."""

import argparse
import re
import subprocess
import sys


FORBIDDEN_URL_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com/Azure/azure-rest-api-specs/[A-Za-z0-9._/-]+/arm-compute/quickstart-templates/aliases\.json"
)
RECOMMENDED_ALIAS_URL = "https://azcliprod.blob.core.windows.net/cli/vm/aliases.json"


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
        if FORBIDDEN_URL_PATTERN.search(added_line):
            violations.append((current_file or "<unknown>", added_line.strip()))

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check diff for forbidden raw aliases URL usage.")
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
        print("No forbidden aliases source URL found in added lines.")
        return 0

    print("Found forbidden aliases source URL in this change:", file=sys.stderr)
    for file_path, content in violations:
        print(f"  - {file_path}: {content}", file=sys.stderr)

    print(
        f"Use '{RECOMMENDED_ALIAS_URL}' instead of raw GitHub URLs for aliases.json.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())

