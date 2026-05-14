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


GITHUB_URL_PATTERN = re.compile(
    r"https?://raw\.githubusercontent\.com/[^\s\"'`,)}\]]*"
)
INLINE_SUPPRESSION_PATTERN = re.compile(
    r"#\s*external-url-exempt:\s*\S"
)
_FILENAME_PATTERN = re.compile(r"^[A-Za-z0-9_\-]+\.[A-Za-z0-9]{1,10}$")
RECOMMENDED_INTERNAL_URL = "https://azcliprod.blob.core.windows.net/cli"
SCOPE_CONFIG_PATH = Path(__file__).with_name("external_url_exclusions.json")

# Scope configuration loaded from external_url_exclusions.json.
# Contains optional "include" and "exclude" glob-pattern lists.
_SCOPE_CONFIG = None


def _load_scope_config():
    """Load scope configuration (include/exclude patterns) from the JSON file."""
    try:
        with SCOPE_CONFIG_PATH.open(encoding="utf-8") as input_file:
            config = json.load(input_file)
    except (OSError, ValueError) as ex:
        raise RuntimeError(f"Unable to load scope config from '{SCOPE_CONFIG_PATH}': {ex}") from ex

    if not isinstance(config, dict):
        raise RuntimeError(
            f"Invalid scope configuration in '{SCOPE_CONFIG_PATH}': expected a JSON object"
        )

    scope = config.get("scope", {})
    if not isinstance(scope, dict):
        raise RuntimeError(
            f"Invalid scope configuration in '{SCOPE_CONFIG_PATH}': 'scope' must be a JSON object"
        )

    include = scope.get("include", [])
    exclude = scope.get("exclude", [])

    if isinstance(include, str):
        include = [include]
    if isinstance(exclude, str):
        exclude = [exclude]

    if not isinstance(include, list) or not all(isinstance(p, str) for p in include):
        raise RuntimeError(
            f"Invalid scope configuration in '{SCOPE_CONFIG_PATH}': 'include' must be a string or array of strings"
        )
    if not isinstance(exclude, list) or not all(isinstance(p, str) for p in exclude):
        raise RuntimeError(
            f"Invalid scope configuration in '{SCOPE_CONFIG_PATH}': 'exclude' must be a string or array of strings"
        )

    return (
        [p.replace("\\", "/") for p in include],
        [p.replace("\\", "/") for p in exclude],
    )


def _get_scope_config():
    """Return cached (include_patterns, exclude_patterns) tuple."""
    global _SCOPE_CONFIG  # pylint: disable=global-statement

    if _SCOPE_CONFIG is None:
        _SCOPE_CONFIG = _load_scope_config()

    return _SCOPE_CONFIG


def _matches_any(file_path: str, patterns: list) -> bool:
    """Return True if *file_path* matches any of the given glob patterns."""
    return any(fnmatch.fnmatch(file_path, p) for p in patterns)



def _extract_filename_from_url(line: str) -> str:
    """Extract the file name from the first GitHub URL found in *line*.

    Returns the basename (e.g. ``map.json``) or ``"xxx.xxx"`` when no
    recognisable file name is present.
    """
    match = GITHUB_URL_PATTERN.search(line)
    if match:
        url_path = match.group(0).rstrip("/")
        basename = url_path.rsplit("/", 1)[-1] if "/" in url_path else ""
        if _FILENAME_PATTERN.match(basename):
            return basename
    return "xxx.xxx"


def _should_flag(file_path: str) -> bool:
    """Decide whether *file_path* should be checked for forbidden URLs.

    An entry is included when there is no include list (empty means
    "entire codebase") or when it matches at least one include pattern.
    A included entry is then flagged unless it also matches an exclude pattern.
    """
    include_patterns, exclude_patterns = _get_scope_config()

    included = (not include_patterns) or _matches_any(file_path, include_patterns)
    return included and not _matches_any(file_path, exclude_patterns)


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
    prev_added_line = ""

    for line in diff_text.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            prev_added_line = ""
            continue

        if not line.startswith("+") or line.startswith("+++"):
            prev_added_line = ""
            continue

        added_line = line[1:]
        if GITHUB_URL_PATTERN.search(added_line) and _should_flag(current_file):
            # Skip if the current line or the previous added line has a suppression comment
            if not (INLINE_SUPPRESSION_PATTERN.search(added_line)
                    or INLINE_SUPPRESSION_PATTERN.search(prev_added_line)):
                violations.append((current_file or "<unknown>", added_line.strip()))

        prev_added_line = added_line

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description="Check diff for forbidden raw GitHub URL usage.")
    parser.add_argument("--src", default="HEAD", help="Source ref/commit for git diff.")
    parser.add_argument("--tgt", default="HEAD~1", help="Target ref/commit for git diff.")
    parser.add_argument("--cached", action="store_true", help="Check staged changes in git index.")
    args = parser.parse_args()

    try:
        _get_scope_config()
        diff_text = _run_diff(src=args.src, tgt=args.tgt, cached=args.cached)
    except Exception as ex:  # pylint: disable=broad-except
        if args.cached:
            print(f"Unable to evaluate staged diff: {ex}", file=sys.stderr)
        else:
            print(f"Unable to evaluate diff between '{args.tgt}' and '{args.src}': {ex}", file=sys.stderr)
        return 1

    violations = _find_violations(diff_text)
    if not violations:
        print("No forbidden external GitHub URL found in added lines.")
        return 0

    print("ERROR: Found forbidden external GitHub URL(s) in this change:\n", file=sys.stderr)
    for file_path, content in violations:
        filename = _extract_filename_from_url(content)
        print(
            f"  {file_path}: {content}\n"
            "\n"
            "  To fix, follow one of the options below (in priority order):\n"
            "\n"
            "    Option 1 (Preferred) — Host the file in the AME storage account\n"
            "    ---------------------------------------------------------------\n"
            "    Reach out to the Platform squad to upload the file to the shared\n"
            "    Azure CLI storage account. Once uploaded, replace the raw GitHub\n"
            "    URL with the internal blob URL. The resulting URL should look like:\n"
            "\n"
            f"      {RECOMMENDED_INTERNAL_URL}/<module>/{filename}\n"
            "\n"
            "    Option 2 (Fallback) — Suppress with an inline comment\n"
            "    -----------------------------------------------------\n"
            "    Only if the GitHub URL is required by design (e.g. the upstream\n"
            "    repo IS the authoritative source), add an inline suppression\n"
            "    comment on the line before or on the same line like:\n"
            "\n"
            "      # external-url-exempt: <reason>\n"
            f"     {content} \n",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())

