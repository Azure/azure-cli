# pylint: disable=no-self-use
from __future__ import print_function
import os
import pip
from six.moves import input #pylint: disable=redefined-builtin

from azure.cli.parser import IncorrectUsageError
from azure.cli._locale import L

from azure.cli.utils.update_checker import check_for_component_update

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

PRIVATE_PYPI_URL_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_URL'
PRIVATE_PYPI_URL = os.environ.get(PRIVATE_PYPI_URL_ENV_NAME)
PRIVATE_PYPI_HOST_ENV_NAME = 'AZURE_CLI_PRIVATE_PYPI_HOST'
PRIVATE_PYPI_HOST = os.environ.get(PRIVATE_PYPI_HOST_ENV_NAME)

def _install_or_update(component_name, version, link, private, upgrade=False):
    if not component_name:
        raise IncorrectUsageError(L('Specify a component name.'))
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == COMPONENT_PREFIX + component_name])
    if found and not upgrade:
        raise RuntimeError("Component already installed.")
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
                raise RuntimeError('{} environment variable not set.'
                                   .format(PRIVATE_PYPI_URL_ENV_NAME))
            if not PRIVATE_PYPI_HOST:
                raise RuntimeError('{} environment variable not set.'
                                   .format(PRIVATE_PYPI_HOST_ENV_NAME))
            pkg_index_options += ['--extra-index-url', PRIVATE_PYPI_URL,
                                  '--trusted-host', PRIVATE_PYPI_HOST]
        pip.main(['install'] + options + [COMPONENT_PREFIX + component_name+version_no]
                 + pkg_index_options)

class ComponentCommands(object):

    def __init__(self, **_):
        pass

    def list(self):
        ''' List the installed components.'''
        return sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''), 'version': dist.version}
                       for dist in pip.get_installed_distributions(local_only=True)
                       if dist.key.startswith(COMPONENT_PREFIX)], key=lambda x: x['name'])

    def install(self, component_name, link, private=False, version=None):
        ''' Install a component'''
        _install_or_update(component_name, version, link, private, upgrade=False)

    def update(self, component_name, link, private=False):
        ''' Update a component'''
        _install_or_update(component_name, None, link, private, upgrade=True)

    def update_self(self, private=False):
        ''' Update the CLI'''
        pkg_index_options = []
        if private:
            if not PRIVATE_PYPI_URL:
                raise RuntimeError('{} environment variable not set.'
                                   .format(PRIVATE_PYPI_URL_ENV_NAME))
            if not PRIVATE_PYPI_HOST:
                raise RuntimeError('{} environment variable not set.'
                                   .format(PRIVATE_PYPI_HOST_ENV_NAME))
            pkg_index_options += ['--extra-index-url', PRIVATE_PYPI_URL,
                                  '--trusted-host', PRIVATE_PYPI_HOST]
        pip.main(['install', '--quiet', '--isolated', '--disable-pip-version-check', '--upgrade']
                 + [CLI_PACKAGE_NAME] + pkg_index_options)

    def update_all(self, link, private=False):
        ''' Update all components'''
        component_names = [dist.key.replace(COMPONENT_PREFIX, '')
                           for dist in pip.get_installed_distributions(local_only=True)
                           if dist.key.startswith(COMPONENT_PREFIX)]
        for name in component_names:
            _install_or_update(name, None, link, private, upgrade=True)

    def check_component(self, component_name, private=False):
        ''' Check a component for an update'''
        found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                      if dist.key == COMPONENT_PREFIX + component_name])
        if not found:
            raise RuntimeError(L("Component not installed."))
        update_status = check_for_component_update(component_name, private)
        result = {}
        result['currentVersion'] = str(update_status['current_version'])
        result['latestVersion'] = str(update_status['latest_version'])
        result['updateAvailable'] = update_status['update_available']
        return result

    def remove(self, component_name, force=False):
        ''' Remove a component'''
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
            raise RuntimeError(L("Component not installed."))
