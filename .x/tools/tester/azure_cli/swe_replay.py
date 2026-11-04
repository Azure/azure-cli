# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""SWE replay environment for azure-cli checkouts."""

import posixpath

PACKAGES = ("azure-cli-telemetry", "azure-cli-core", "azure-cli", "azure-cli-testsdk")
ENV = {"AZURE_CORE_COLLECT_TELEMETRY": "false"}


def pip_install(python, *args):
    return [python, "-m", "pip", "install", "-q", "--disable-pip-version-check", *args]


def environment(case, root, python, options=None):
    """Install the checkout's own azure-cli packages into a per-case venv."""
    if case.get("test_framework") != "pytest":
        return None
    venv = posixpath.join(posixpath.dirname(root.rstrip("/")), "venv")
    venv_python = posixpath.join(venv, "bin", "python")
    return {
        "commands": [
            [python, "-m", "venv", venv],
            pip_install(venv_python, "pytest", "setuptools", "wheel"),
            pip_install(venv_python, *(f"--editable=src/{name}" for name in PACKAGES)),
        ],
        "python": venv_python,
        "env": dict(ENV),
    }
