# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Install the CLI under test and provide its resolved pip inventory to CG."""

import platform
import subprocess
import sys
from pathlib import Path


def install_with_report(root):
    src = root / "src"
    projects = sorted(manifest.parent for manifest in src.rglob("pyproject.toml")
                      if "azure-cli-testsdk" not in manifest.relative_to(src).parts)
    if src / "azure-cli" not in projects:
        raise ValueError("Missing local azure-cli project; refusing to resolve azure-cli from an index")

    system = platform.system()
    platform_file = "windows" if system == "Windows" else system
    pins = src / "azure-cli" / f"requirements.py3.{platform_file}.txt"

    # PipReport discovers a pre-generated report beside a file named requirements.txt.
    inventory = root / "cg-runtime-inventory"
    inventory.mkdir(exist_ok=True)
    requirements = inventory / "requirements.txt"
    requirements.write_text("azure-cli\n", encoding="utf-8")

    # One transaction captures the local projects as well as their dependencies;
    # installed agent packages must not silently disappear from the pip report.
    subprocess.run([
        sys.executable, "-m", "pip", "install", "--ignore-installed",
        "--report", str(inventory / "component-detection-pip-report.json"),
        "-r", str(requirements), "-r", str(pins),
        *map(str, projects),
    ], check=True)


if __name__ == "__main__":
    install_with_report(Path(__file__).resolve().parents[2])
