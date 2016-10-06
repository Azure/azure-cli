#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError
from azure.cli.core._config import az_config

CLI_PACKAGE_NAME = 'azure-cli'
COMPONENT_PREFIX = 'azure-cli-'

def list_components():
    """ List the installed components """
    import pip
    return sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''), 'version': dist.version}
                   for dist in pip.get_installed_distributions(local_only=True)
                   if dist.key.startswith(COMPONENT_PREFIX)], key=lambda x: x['name'])

def remove(component_name, show_logs=False):
    """ Remove a component """
    import pip
    full_component_name = COMPONENT_PREFIX + component_name
    found = bool([dist for dist in pip.get_installed_distributions(local_only=True)
                  if dist.key == full_component_name])
    if found:
        options = ['--isolated', '--yes']
        options += [] if show_logs else ['--quiet']
        pip.main(['uninstall'] + options + ['--disable-pip-version-check', full_component_name])
    else:
        raise CLIError("Component not installed.")

def _install_or_update(package_list, link, private, pre, show_logs=False):
    import pip
    options = ['--isolated', '--disable-pip-version-check', '--upgrade']
    if pre:
        options.append('--pre')
    if not show_logs:
        options.append('--quiet')
    pkg_index_options = ['--find-links', link] if link else []
    if private:
        package_index_url = az_config.get('component', 'package_index_url', fallback=None)
        package_index_trusted_host = az_config.get('component', 'package_index_trusted_host', fallback=None) #pylint: disable=line-too-long
        if package_index_url:
            pkg_index_options += ['--extra-index-url', package_index_url]
        else:
            raise CLIError('AZURE_COMPONENT_PACKAGE_INDEX_URL environment variable not set and not specified in config. ' #pylint: disable=line-too-long
                           'AZURE_COMPONENT_PACKAGE_INDEX_TRUSTED_HOST may also need to be set.') #pylint: disable=line-too-long
        pkg_index_options += ['--trusted-host', package_index_trusted_host] if package_index_trusted_host else [] #pylint: disable=line-too-long
    pip.main(['install'] + options + package_list
             + pkg_index_options)

def update(private=False, pre=False, link=None, additional_component=None, show_logs=False):
    """ Update the CLI and all installed components """
    import pip
    package_list = [CLI_PACKAGE_NAME]
    package_list += [dist.key for dist in pip.get_installed_distributions(local_only=True)
                     if dist.key.startswith(COMPONENT_PREFIX)]
    if additional_component:
        package_list += [COMPONENT_PREFIX + additional_component]
    _install_or_update(package_list, link, private, pre, show_logs=show_logs)
