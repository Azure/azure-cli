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

DEFAULT_TEMPLATE = "scripts/release/standalone/templates/azure-cli.rb.in"
DEFAULT_OUTPUT = "azure-cli.rb"


def _env_or_arg(value: str, env_key: str) -> str:
    return value if value is not None else os.environ.get(env_key)


def _require(value: str, name: str) -> str:
    if not value:
        raise SystemExit(f"Missing required value: {name}")
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

    content = _render_template(template_path, replacements)
    output_path.write_text(content)


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
    parser.set_defaults(func=generate_cask)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
