#!/usr/bin/env python

# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Fail CI if forbidden raw GitHub URL is introduced in new diff lines."""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path


FORBIDDEN_EXTERNAL_URL_PATTERN = re.compile(
    r"https://raw\.githubusercontent\.com"
)
RECOMMENDED_INTERNAL_URL = "https://azcliprod.blob.core.windows.net/cli"
EXCLUSION_CONFIG_PATH = Path(__file__).with_name("external_url_exclusions.json")

# Paths matching these glob patterns are excluded from the check.
# Exclusions are loaded from external_url_exclusions.json.
EXCLUDED_PATH_PATTERNS = None


def _load_excluded_path_patterns():
    """Load excluded path glob patterns from the JSON configuration file."""
    try:
        with EXCLUSION_CONFIG_PATH.open(encoding="utf-8") as input_file:
            config = json.load(input_file)
    except (OSError, ValueError) as ex:
        raise RuntimeError(f"Unable to load exclusion patterns from '{EXCLUSION_CONFIG_PATH}': {ex}") from ex

    if not isinstance(config, dict):
        raise RuntimeError(
            f"Invalid exclusion pattern configuration in '{EXCLUSION_CONFIG_PATH}': expected a JSON object"
        )

    exclusions = config.get("exclusions")
    if not isinstance(exclusions, list):
        raise RuntimeError(
            f"Invalid exclusion pattern configuration in '{EXCLUSION_CONFIG_PATH}': expected 'exclusions' to be a JSON array"
        )

    patterns = []
    for exclusion in exclusions:
        if not isinstance(exclusion, dict):
            raise RuntimeError(
                f"Invalid exclusion pattern configuration in '{EXCLUSION_CONFIG_PATH}': each exclusion must be a JSON object"
            )

        files = exclusion.get("file")
        if isinstance(files, str):
            files = [files]

        if not isinstance(files, list) or not all(isinstance(pattern, str) for pattern in files):
            raise RuntimeError(
                f"Invalid exclusion pattern configuration in '{EXCLUSION_CONFIG_PATH}': each exclusion 'file' must be a string or JSON array of strings"
            )

        patterns.extend(pattern.replace("\\", "/") for pattern in files)

    return patterns


def _get_excluded_path_patterns():
    """Return cached excluded path glob patterns."""
    global EXCLUDED_PATH_PATTERNS  # pylint: disable=global-statement

    if EXCLUDED_PATH_PATTERNS is None:
        EXCLUDED_PATH_PATTERNS = _load_excluded_path_patterns()

    return EXCLUDED_PATH_PATTERNS


def _is_excluded(file_path: str) -> bool:
    """Return True if *file_path* matches one of the exclusion glob patterns."""
    for pattern in _get_excluded_path_patterns():
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
        _get_excluded_path_patterns()
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

