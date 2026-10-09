# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Read source package versions without importing the CLI or invoking a build."""

import ast
from pathlib import Path
import subprocess
import sys
import tokenize

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib


_RUNTIME_VERSION_FILES = {
    'azure-cli': 'azure/cli/__main__.py',
    'azure-cli-core': 'azure/cli/core/__init__.py',
}


def _check_runtime_version(package_path, name, version):
    relative_path = _RUNTIME_VERSION_FILES.get(name)
    if relative_path is None:
        return

    runtime_path = package_path / relative_path
    try:
        with tokenize.open(runtime_path) as source:
            tree = ast.parse(source.read(), filename=str(runtime_path))
    except (OSError, SyntaxError) as error:
        raise ValueError('Unable to read runtime __version__ for {} from {}: {}'.format(
            name, runtime_path, error)) from error

    values = []
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, ast.AnnAssign):
            targets = [statement.target]
        else:
            continue
        if any(isinstance(target, ast.Name) and target.id == '__version__' for target in targets):
            values.append(statement.value)

    if (len(values) != 1 or not isinstance(values[0], ast.Constant)
            or not isinstance(values[0].value, str)):
        raise ValueError('Expected one top-level string literal __version__ in {}'.format(runtime_path))
    runtime_version = values[0].value
    if runtime_version != version:
        raise ValueError(
            'Version mismatch for {}: {} [project].version is {!r}, but {} __version__ is {!r}. '
            'Update both source versions together.'.format(
                name, package_path / 'pyproject.toml', version, runtime_path, runtime_version))


def get_package_version(package_path):
    """Prefer static PEP 621 metadata; retain setup.py for historical checkouts.

    Invalid modern metadata must fail rather than silently falling back to setup.py.
    The main/core runtime literals are checked here so every source-version consumer
    retains the validation previously performed by their setup scripts.
    """
    package_path = Path(package_path)
    pyproject_path = package_path / 'pyproject.toml'
    if pyproject_path.is_file():
        try:
            with pyproject_path.open('rb') as source:
                metadata = tomllib.load(source)
        except ValueError as error:
            raise ValueError('Invalid TOML in {}: {}'.format(pyproject_path, error)) from error
        project = metadata.get('project', {})
        name = project.get('name')
        version = project.get('version')
        if not isinstance(name, str) or not name.strip():
            raise ValueError('Expected a non-empty [project].name in {}'.format(pyproject_path))
        if (not isinstance(version, str) or not version.strip()
                or 'version' in project.get('dynamic', [])):
            raise ValueError('Expected a static, non-empty [project].version in {}'.format(pyproject_path))
        _check_runtime_version(package_path, name, version)
        return version

    setup_path = package_path / 'setup.py'
    if not setup_path.is_file():
        raise FileNotFoundError('No pyproject.toml or setup.py found in {}'.format(package_path))
    return subprocess.check_output(
        [sys.executable, 'setup.py', '--version'], cwd=str(package_path),
        universal_newlines=True).strip()