# pylint: disable=no-self-use
from __future__ import print_function
import os
import pip
from six.moves import input #pylint: disable=redefined-builtin

from azure.cli.parser import IncorrectUsageError
from azure.cli.help_files import helps
from azure.cli.utils.update_checker import check_for_component_update
from azure.cli._util import CLIError

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

PRIVATE_PYPI_URL_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_URL'
PRIVATE_PYPI_URL = os.environ.get(PRIVATE_PYPI_URL_ENV_NAME)
PRIVATE_PYPI_HOST_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_HOST'
PRIVATE_PYPI_HOST = os.environ.get(PRIVATE_PYPI_HOST_ENV_NAME)

def _install_or_update(component_name, version, link, private, upgrade=False):
    if not component_name:
        raise IncorrectUsageError('Specify a component name.')
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX + component_name])
    if found and not upgrade:
        raise CLIError("Component already installed.")
    else:
        version_no = '==' + version if version else ''
        options = ['--quiet', '--isolated', '--disable-pip-version-check']
        if upgrade:
            options.append('--upgrade')
        pkg_index_options = []
        if link:
            pkg_index_options += ['--find-links', link]
        if private:
            if not PRIVATE_PYPI_URL:
                raise CLIError('{} environment variable not set.'
                               .format(PRIVATE_PYPI_URL_ENV_NAME))
            if not PRIVATE_PYPI_HOST:
                raise CLIError('{} environment variable not set.'
                               .format(PRIVATE_PYPI_HOST_ENV_NAME))
            pkg_index_options += ['--extra-index-url', PRIVATE_PYPI_URL,
                                  '--trusted-host', PRIVATE_PYPI_HOST]
        pip.main(['install'] + options + [COMPONENT_PREFIX + component_name+version_no]
                 + pkg_index_options)

helps['component list'] = """
    short-summary: List the installed components
"""
def list_components():
    return sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''), 'version': dist.version}
                   for dist in pip.get_installed_distributions(local_only=True)
                   if dist.key.startswith(COMPONENT_PREFIX)], key=lambda x: x['name'])

helps['component install'] = """
    short-summary: Install a component
    parameters:
        - name: --name -n
          short-summary: The component name to install.
"""
def install(component_name, link=None, private=False, version=None):
    _install_or_update(component_name, version, link, private, upgrade=False)

helps['component update'] = """
    short-summary: Update a component
    parameters:
        - name: --name -n
          short-summary: The component name to update.
"""
def update(component_name, link=None, private=False):
    _install_or_update(component_name, None, link, private, upgrade=True)

helps['component update-self'] = """
    short-summary: Update the CLI
"""
def update_self(private=False):
    pkg_index_options = []
    if private:
        if not PRIVATE_PYPI_URL:
            raise CLIError('{} environment variable not set.'
                           .format(PRIVATE_PYPI_URL_ENV_NAME))
        if not PRIVATE_PYPI_HOST:
            raise CLIError('{} environment variable not set.'
                           .format(PRIVATE_PYPI_HOST_ENV_NAME))
        pkg_index_options += ['--extra-index-url', PRIVATE_PYPI_URL,
                              '--trusted-host', PRIVATE_PYPI_HOST]
    pip.main(['install', '--quiet', '--isolated', '--disable-pip-version-check', '--upgrade']
             + [CLI_PACKAGE_NAME] + pkg_index_options)

helps['component update-all'] = """
    short-summary: Update all components
"""
def update_all(link=None, private=False):
    component_names = [dist.key.replace(COMPONENT_PREFIX, '')
                       for dist in pip.get_installed_distributions(local_only=True)
                       if dist.key.startswith(COMPONENT_PREFIX)]
    for name in component_names:
        _install_or_update(name, None, link, private, upgrade=True)

helps['component check'] = """
    short-summary: Check a component for an update
    parameters:
        - name: --name -n
          short-summary: The component name to check.
"""
def check_component(component_name, private=False):
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX + component_name])
    if not found:
        raise CLIError("Component not installed.")
    update_status = check_for_component_update(component_name, private)
    result = {}
    result['currentVersion'] = str(update_status['current_version'])
    result['latestVersion'] = str(update_status['latest_version'])
    result['updateAvailable'] = update_status['update_available']
    return result

helps['component remove'] = """
    short-summary: Remove a component
    parameters:
        - name: --name -n
          short-summary: The component name to remove.
"""
def remove(component_name, force=False):
    prompt_for_delete = force is None
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX + component_name])
    if found:
        if prompt_for_delete:
            ans = input("Really delete '{}'? [y/N] ".format(component_name))
            if not ans or ans[0].lower() != 'y':
                return
        pip.main(['uninstall', '--quiet', '--isolated', '--yes',
                  '--disable-pip-version-check', COMPONENT_PREFIX + component_name])
    else:
        raise CLIError("Component not installed.")
