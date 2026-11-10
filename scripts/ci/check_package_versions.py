# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Validate source versions before building release or nightly distributions."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKAGES = ('azure-cli', 'azure-cli-core', 'azure-cli-telemetry', 'azure-cli-testsdk')
sys.path.insert(0, str(ROOT / 'tools'))

from automation.utilities.packaging import get_package_version, tomllib  # noqa: E402


def main():
    versions = {}
    for name in PACKAGES:
        versions[name] = get_package_version(ROOT / 'src' / name)
    with (ROOT / 'src/azure-cli/pyproject.toml').open('rb') as stream:
        dependencies = tomllib.load(stream)['project']['dependencies']
    expected = 'azure-cli-core==' + versions['azure-cli-core']
    if expected not in dependencies or versions['azure-cli'] != versions['azure-cli-core']:
        raise ValueError('CLI and core versions must match, including the dependency: ' + expected)
    for name, version in versions.items():
        print('{}: {}'.format(name, version))


if __name__ == '__main__':
    main()