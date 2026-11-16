#!/usr/bin/env python3
# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Generate the Homebrew cask from a template.

Usage:
    python3 scripts/release/standalone/cask_generate.py \
        --version "2.x.y" \
        --arm64-macos-sha "<macos arm64 sha256>" \
        --x86-64-macos-sha "<macos x86_64 sha256>" \
        --arm64-linux-sha "<linux arm64 sha256>" \
        --x86-64-linux-sha "<linux x86_64 sha256>" \
        --github-repo "Azure/azure-cli" \
        --template "scripts/release/standalone/templates/azure-cli.rb.in" \
        --output "azure-cli.rb"

Environment variable fallbacks (used when a CLI flag is omitted):
    VERSION, ARM64_MACOS_SHA, X86_64_MACOS_SHA, ARM64_LINUX_SHA, X86_64_LINUX_SHA,
    GITHUB_REPO, TEMPLATE, OUTPUT
"""

import argparse
import os
from pathlib import Path
import re

DEFAULT_TEMPLATE = "scripts/release/standalone/templates/azure-cli.rb.in"
DEFAULT_OUTPUT = "azure-cli.rb"
FIELD_PATTERNS = {
    "version": r"[0-9]+\.[0-9]+\.[0-9]+(?:[a-z][a-z0-9]*)?",
    "arm64_macos_sha": r"[0-9a-fA-F]{64}",
    "x86_64_macos_sha": r"[0-9a-fA-F]{64}",
    "arm64_linux_sha": r"[0-9a-fA-F]{64}",
    "x86_64_linux_sha": r"[0-9a-fA-F]{64}",
    "github_repo": r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_.-]+",
    "python_version": r"3\.[0-9]+",
}


def _env_or_arg(value: str, env_key: str) -> str:
    return value if value is not None else os.environ.get(env_key)


def _require(value: str, name: str) -> str:
    if not value:
        raise SystemExit(f"Missing required value: {name}")
    return value


def _validate_value(value: str, name: str) -> str:
    if not re.fullmatch(FIELD_PATTERNS[name], value, flags=re.ASCII):
        raise SystemExit(f"Invalid value for {name}")
    return value


def _render_template(template_path: Path, replacements: dict[str, str]) -> str:
    content = template_path.read_text()
    for key, value in replacements.items():
        content = content.replace(key, value)

    if "{{" in content:
        raise SystemExit("Template placeholders not fully replaced")
    if not content.endswith("\n"):
        content += "\n"
    return content


def generate_cask(args: argparse.Namespace) -> None:
    version = _require(_env_or_arg(args.version, "VERSION"), "version")
    arm64_macos_sha = _require(_env_or_arg(args.arm64_macos_sha, "ARM64_MACOS_SHA"), "arm64_macos_sha")
    x86_64_macos_sha = _require(_env_or_arg(args.x86_64_macos_sha, "X86_64_MACOS_SHA"), "x86_64_macos_sha")
    arm64_linux_sha = _require(_env_or_arg(args.arm64_linux_sha, "ARM64_LINUX_SHA"), "arm64_linux_sha")
    x86_64_linux_sha = _require(_env_or_arg(args.x86_64_linux_sha, "X86_64_LINUX_SHA"), "x86_64_linux_sha")
    github_repo = _require(_env_or_arg(args.github_repo, "GITHUB_REPO"), "github_repo")
    python_version = _require(_env_or_arg(args.python_version, "PYTHON_VERSION"), "python_version")

    template_path = Path(_env_or_arg(args.template, "TEMPLATE") or DEFAULT_TEMPLATE)
    output_path = Path(_env_or_arg(args.output, "OUTPUT") or DEFAULT_OUTPUT)

    replacements = {
        "{{ version }}": version,
        "{{ arm64_macos_sha }}": arm64_macos_sha,
        "{{ x86_64_macos_sha }}": x86_64_macos_sha,
        "{{ arm64_linux_sha }}": arm64_linux_sha,
        "{{ x86_64_linux_sha }}": x86_64_linux_sha,
        "{{ github_repo }}": github_repo,
        "{{ python_version }}": python_version,
    }
    for key, value in replacements.items():
        _validate_value(value, key[3:-3])

    content = _render_template(template_path, replacements)
    output_path.write_text(content)


def validate_cask(cask_path: Path, template_path: Path, github_repo: str, python_version: str) -> None:
    """Check the complete publication source without evaluating Ruby."""
    _validate_value(github_repo, "github_repo")
    _validate_value(python_version, "python_version")
    template = template_path.read_text()
    if not template.endswith("\n"):
        template += "\n"
    pattern = re.escape(template)
    for name, field_pattern in FIELD_PATTERNS.items():
        placeholder = "{{ " + name + " }}"
        if template.count(placeholder) != 1:
            raise SystemExit(f"Expected one template placeholder for {name}")
        pattern = pattern.replace(re.escape(placeholder), f"(?P<{name}>{field_pattern})")
    match = re.fullmatch(pattern, cask_path.read_text(), flags=re.ASCII)
    if match is None:
        raise SystemExit("Cask does not match the trusted template and validated field formats")
    if match["github_repo"] != github_repo or match["python_version"] != python_version:
        raise SystemExit("Cask repository or Python version does not match the pipeline settings")
    print(f"Validated publication cask: {cask_path}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cask_generate.py")
    parser.add_argument("--version", dest="version", help="Azure CLI version")
    parser.add_argument("--arm64-macos-sha", dest="arm64_macos_sha", help="macOS ARM64 tarball SHA256")
    parser.add_argument("--x86-64-macos-sha", dest="x86_64_macos_sha", help="macOS x86_64 tarball SHA256")
    parser.add_argument("--arm64-linux-sha", dest="arm64_linux_sha", help="Linux ARM64 tarball SHA256")
    parser.add_argument("--x86-64-linux-sha", dest="x86_64_linux_sha", help="Linux x86_64 tarball SHA256")
    parser.add_argument("--github-repo", dest="github_repo", help="GitHub repo, e.g. Azure/azure-cli")
    parser.add_argument("--python-version", dest="python_version", help="Python major.minor version, e.g. 3.14")
    parser.add_argument("--template", dest="template", help="Template path (.rb.in)")
    parser.add_argument("--output", dest="output", help="Output cask path (.rb)")
    parser.add_argument("--validate", metavar="CASK", help="Validate an existing publication cask without evaluating Ruby")
    parser.set_defaults(func=generate_cask)

    args = parser.parse_args()
    if args.validate:
        validate_cask(
            Path(args.validate),
            Path(_env_or_arg(args.template, "TEMPLATE") or DEFAULT_TEMPLATE),
            _require(_env_or_arg(args.github_repo, "GITHUB_REPO"), "github_repo"),
            _require(_env_or_arg(args.python_version, "PYTHON_VERSION"), "python_version"),
        )
    else:
        args.func(args)


if __name__ == "__main__":
    main()
